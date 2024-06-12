import typing as t
import asyncio
from os import getcwd
from os.path import join as osJoin, getsize

HEADER_BYTES = 18
ARGS_BYTES = 256

# colores
RESET = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"

class ITP:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, path_files: str = "files") -> None:
        self.reader:asyncio.StreamReader = reader
        self.writer:asyncio.StreamWriter = writer
        self._path_files = path_files

        self.FUNCTIONS = {
            '-file': self.send_file,
            'rfile': self._get_file,
            '-gfile': self.descargar_file,
            '-cmd': self._cmd,
            'close': self.close
        }
        self.builtint_func: set = set(self.FUNCTIONS.keys())

    async def send_file(self, filename: bytes) -> None:
        filename_ = filename.decode().strip()
        try:
            ruta = osJoin(getcwd(), self._path_files, filename_)
            size = getsize(ruta)
        except FileNotFoundError as e:
            return await self.enviar_error(f"{e}".encode(), "719")

        size_bytes = size.to_bytes(8, byteorder='little')
        args = self.empaquetar_args(filename, size_bytes)
        header = self.crear_header(size + len(filename) + len(args), "rfile")
        await self._enviar_datos(header + args)

        print(f"{YELLOW}[+]\tenviando archivo...{RESET}")
        with open(ruta, "rb") as f:
            await self._enviar_datos(f.read())
        print(f"{GREEN}[+]\tArchivo enviado{RESET}")

    async def _get_file(self, filename: t.Union[str, bytes], size: t.Union[int, bytes]):
        if type(size) == bytes:
            size = int.from_bytes(size, byteorder='little')
        if type(filename) == bytes:
            filename = filename.decode()
        filename = filename.strip()

        print(f"{YELLOW}[+]\tRecibiendo archivo...{RESET}")
        path = osJoin(getcwd(), self._path_files, filename)
        contenido = await self._obtener_contenido(int(size))
        with open(path, "wb") as f:
            f.write(contenido)
        print(f"{GREEN}[+]\tArchivo recibido{RESET}")

    async def _cmd(self, cmd: bytes) -> None:
        cmd = cmd.decode().strip()
        try:
            proceso = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proceso.communicate()
            res = stdout if stdout else stderr
            if stderr:
                await self.enviar_error(res.decode(), "c13")
            else:
                await self._enviar_datos(self.crear_header(len(res), "A2") + res)

        except Exception as e:
            await self.enviar_error(str(e), "c13")

    async def descargar_file(self, filename: t.Union[str, bytes]):
        await self.exec_cmd("-file", filename.decode() if type(filename) == bytes else filename)
        await self._enviar_datos(self.crear_header(0, "A1"))

    async def close(self):
        await self._enviar_datos(self.crear_header(0, "close"))
        self.writer.close()
        await self.writer.wait_closed()

    async def empaquetar_args(self, *args):
        return b"args|" + b" ".join(args).ljust(ARGS_BYTES, b'\0')

    def crear_header(self, longitud: int, comando: str):
        longitud = min(longitud, 10**12 - 1)

        longitud_bytes: bytes = longitud.to_bytes(8, byteorder='little')
        comando_bytes: bytes = comando.encode('utf-8')

        header: bytes = longitud_bytes + b'|' + comando_bytes
        header = header.ljust(HEADER_BYTES, b'\0')

        return header

    async def _obtener_args(self, longitud: int) -> t.Tuple[bytes]:
        if longitud > ARGS_BYTES:
            cmd_args = await self.reader.readexactly(5)
            if cmd_args == b"args|":
                return (await self.reader.readexactly(ARGS_BYTES)).rstrip(b"\0").split(b" ")
            return (cmd_args + await self._obtener_contenido(longitud - 5),)
        return (await self._obtener_contenido(longitud),)

    async def _obtener_header(self) -> t.Tuple[str, int]:
        try:
            header = await self.reader.readexactly(HEADER_BYTES)
        except asyncio.exceptions.IncompleteReadError:
            print(f"{RED} Cabecera mal formada {RESET}")
            return "", 0
        try:
            longitud_bytes, comando_bytes = header.split(b"|", 1)
            longitud = int.from_bytes(longitud_bytes, byteorder='little')
            comando = comando_bytes.rstrip(b"\0").decode('utf-8')
        except Exception as e:
            await self.enviar_error(str(e).encode(), "H0")
            return "", 0
        return comando, longitud

    async def _enviar_datos(self, data: bytes):
        self.writer.write(data)
        await self.writer.drain()

    async def _obtener_contenido(self, length: int) -> bytes:
        data = b''
        while len(data) < length:
            chunk = await self.reader.read(length - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def _parse_respuesta(self, data: bytes, cmd: str) -> t.Tuple[bytes, str, bool]:
        error = cmd == "error"
        if error:
            codigo, data = data.split(b":", 1)
            return data, codigo.decode(), error
        return data, cmd, error

    async def _obtener_respuesta(self) -> t.Tuple[bytes, str, bool]:
        comando, longitud = await self._obtener_header()
        data = await self._obtener_contenido(longitud) if longitud > 0 else b""
        return self._parse_respuesta(data, comando)

    async def enviar_error(self, msg_error: bytes, codigo: str):
        msg_error = f"{codigo}:{msg_error.decode()}".encode()
        header = self.crear_header(len(msg_error), "error")
        await self._enviar_datos(header + msg_error)

    async def enviar_solicitud(self, cmd: str, data: str) -> t.Union[bytes, None]:
        header = self.crear_header(len(data), cmd)
        await self._enviar_datos(header + data.encode())

        cmd, longitud = await self._obtener_header()
        args = await self._obtener_args(longitud)
        codigo = cmd

        if len(args) == 1:
            res, codigo, error = self._parse_respuesta(args[0], cmd)
            if error:
                return f"{RED}Error [{codigo}]: {res.decode()}{RESET}".encode()
        if self.FUNCTIONS.get(codigo, None):
            if not await self.FUNCTIONS[codigo](*args):
                res, codigo, error = await self._obtener_respuesta()
        return res

    async def exec_cmd(self, cmd: str, data: str) -> t.Union[bytes, None]:
        if cmd == "-file":
            return await self.send_file(data.encode())
        if cmd == "close":
            return await self.close()
        return await self.enviar_solicitud(cmd, data)

    async def enviar_msg(self, data: str) -> t.Union[bytes, None]:
        return await self.enviar_solicitud("txt", data)

    def on(self, cmd: str):
        def wrapper(func):
            self.FUNCTIONS[cmd] = func
            return func
        return wrapper

    async def run(self):
        while True:
            cmd, longitud = await self._obtener_header()
            print(cmd, longitud)
            if not cmd or cmd == "close":
                break
            elif self.FUNCTIONS.get(cmd, None):
                res = self.FUNCTIONS[cmd](*await self._obtener_args(longitud))
                if cmd in self.builtint_func:
                    continue
                res = self.crear_header(len(res), "txt") + res if res else None
                await self._enviar_datos(res or self.crear_header(0, "A1"))
        print(f"{GREEN}[+]\tSe ha cerrado la conexión{RESET}")
        self.writer.close()
        await self.writer.wait_closed()

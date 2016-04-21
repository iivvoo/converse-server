import aiohttp
import aiohttp.server

from .accountmanager import manager


class ConverseWebServer(aiohttp.server.ServerHttpProtocol):
    async def handle_request(self, message, payload):
        # /avatar/token/<acctid>/<backendid>/<userid>
        parts = message.path.split('/')
        status_code = 404
        ct = "text/html"
        msg = b"<h1>Not found</h1>"

        if len(parts) == 6:  # ('', 'avatar', 'token', id, id, id)
            _, ns, token, acctid, backendid, userid = parts
            if ns == 'avatar':
                account = manager.get_by_id(int(acctid))
                be = account.get_backend_by_id(int(backendid))
                user = be.get_user_by_id(int(userid))
                msg = user.get_avatar()
                status_code = 200
                ct = "image/png"

        response = aiohttp.Response(
            self.writer, status_code, http_version=message.version
        )
        response.add_header('Content-Type', ct)
        response.add_header('Content-Length', str(len(msg)))
        response.send_headers()
        response.write(msg)
        await response.write_eof()

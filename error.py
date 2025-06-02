from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse, Response
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


class TreinSchaduwError(Exception):
    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.code,
            content=self.message,
        )

    def to_html(self, request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request, name="error.html",
            context={"error": self.message}
        )

    @staticmethod
    def bad_request(message: str = "Bad request") -> 'TreinSchaduwError':
        return TreinSchaduwError(message, 400)


def exception_handler(request: Request, exc: TreinSchaduwError) -> Response:
    return exc.to_html(request)

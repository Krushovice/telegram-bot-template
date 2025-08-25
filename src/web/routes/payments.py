from fastapi import APIRouter, Request

from web.runtime import runtime

# Импортируй свою реализацию обработчика:
# from your_module import handle_payment_notification

router = APIRouter(tags=["payments"])


@router.post("/payments/callback")
async def payment_callback(request: Request):
    # Пример: проксируем в общий обработчик
    # return await handle_payment_notification(bot=runtime.bot, dp=runtime.dp, request=request)
    # Пока просто заглушка:
    data = await request.json()
    # TODO: валидация подписи провайдера
    # TODO: идемпотентность
    return {"received": True, "size": len(str(data))}

from univention.management.console.resource import Resource
from univention.management.console.log import CORE
from univention.management.console.shared_memory import shared_memory
import asyncio
from tornado.iostream import StreamClosedError


class LogoutNotifier:
    def __init__(self):
        self.event = asyncio.Event()
        self.__count = 0
        self.lock = asyncio.Lock()
        self.wait_task = None

    async def wait(self) -> bool:
        async with self.lock:
            self.__count += 1
        CORE.error("AWAITING the REAL EVENT")
        await self.event.wait()
        CORE.error("WE HAVE BEEN SET THE REAL EVENT")

        return await self.release()

    def set(self):
        self.event.set()

    async def count(self):
        async with self.lock:
            return self.__count

    async def release(self) -> bool:
        async with self.lock:
            self.__count -= 1
            return self.__count == 0


class SSELogoutNotifer(Resource):
    requires_authentication = True
    logout_notifier = None
    wait_task = None
    cancelled = True

    async def wait(self) -> bool:
        if self.logout_notifier is None:
            raise Exception("Logout notifier is none")
        self.wait_task = asyncio.create_task(self.logout_notifier.wait())
        try:
            ret = await self.wait_task
            self.cancelled = False
            return ret
        except asyncio.CancelledError:
            CORE.error("CANCELLED")
            return await self.logout_notifier.release()

    async def get(self):
        CORE.error("SSE_INIT")
        self.set_header('content-type', 'text/event-stream')
        self.set_header('cache-control', 'no-cache')
        self.set_status(200)
        self.write("data:init\n\n")
        await self.flush()

        session_id = self.current_user.session_id
        self.for_session_id = session_id
        CORE.error("server sent event on logout requested for session_id %s" % session_id)

        self.logout_notifier = shared_memory.logout_notifiers.get(session_id, None)

        if self.logout_notifier is None:
            self.logout_notifier = LogoutNotifier()
            shared_memory.logout_notifiers[session_id] = self.logout_notifier

        last = await self.wait()
        self.logout_notifier = None
        CORE.error("server sent event on logout request finished for session_id %s" % session_id)
        if last:
            CORE.error("we are the last ones. Delete logout_notifier from dict")
            shared_memory.logout_notifiers.pop(session_id, None)

        # the connection might have already been closed here, and we might not even have been logged out
        if not self.cancelled:
            try:
                await self.finish("data:logout\n\n")
            except StreamClosedError:
                pass

    def on_connection_close(self):
        CORE.error("ON CONNECTION CLOSE")
        if self.wait_task is not None:
            CORE.error("ON CONNECTION CLOSE LOGOUT_NOTIFIER NOT NONE")
            self.wait_task.cancel()

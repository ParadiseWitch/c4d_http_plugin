# -*- coding: utf-8 -*-
import c4d
import traceback
import Queue as _queue

from constants import MESSAGE_PLUGIN_ID
import routes

_task_queue = None


def get_queue():
    global _task_queue
    if _task_queue is None:
        if _queue is None:
            raise RuntimeError("queue module not available")
        _task_queue = _queue.Queue()
    return _task_queue


def enqueue_task(task):
    q = get_queue()
    q.put(task)
    c4d.SpecialEventAdd(MESSAGE_PLUGIN_ID)


def process_tasks():
    q = get_queue()
    processed = 0
    while True:
        try:
            task = q.get_nowait()
        except Exception:
            break
        action_name = task.get("action")
        fn = routes.ACTIONS.get(action_name)
        if fn is not None:
            result = None
            try:
                result = fn(task.get("payload"))
            except Exception:
                stack = traceback.format_exc()
                print(stack)
                result = {"ok": False, "error": "action-failed", "stack": stack}
            if "event" in task:
                task["result"] = result
                try:
                    task["event"].set()
                except Exception:
                    pass
        processed += 1
    if processed:
        try:
            print("[http] processed %d task(s)" % processed)
        except Exception:
            pass

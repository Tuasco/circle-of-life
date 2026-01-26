#!/usr/bin/env python3
"""
Message Queue wrapper using POSIX message queues.
Provides the same interface as multiprocessing.Queue for compatibility.
"""
import posix_ipc
from typing import Optional


class MessageQueue:
    """
    Wrapper around POSIX message queue with Queue-like interface.

    Args:
        name: Unique name for the message queue (must start with '/').
        create: If True, create the queue. If False, connect to existing.
        max_messages: Maximum number of messages in queue.
        max_message_size: Maximum size of each message in bytes.
    """

    def __init__(
        self,
        name: str,
        create: bool = True,
        max_messages: int = 10,
        max_message_size: int = 8192,
    ):
        self.name = name if name.startswith("/") else f"/{name}"
        self.max_message_size = max_message_size

        flags = posix_ipc.O_CREAT if create else 0
        self.mq = posix_ipc.MessageQueue(
            self.name,
            flags=flags,
            max_messages=max_messages,
            max_message_size=max_message_size,
        )

    def put(self, item: str, timeout: Optional[float] = None) -> None:
        """
        Put an item into the queue.

        Args:
            item: String message to send.
            timeout: Optional timeout in seconds.
        """
        self.mq.send(item.encode("utf-8"), timeout=timeout)

    def get(self, timeout: Optional[float] = None) -> str:
        """
        Get an item from the queue.

        Args:
            timeout: Optional timeout in seconds.

        Returns:
            The message string.
        """
        message, _ = self.mq.receive(timeout=timeout)
        return message.decode("utf-8")

    def close(self) -> None:
        """Close the message queue."""
        self.mq.close()

    def unlink(self) -> None:
        """Remove the message queue from the system."""
        try:
            self.mq.unlink()
        except posix_ipc.ExistentialError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

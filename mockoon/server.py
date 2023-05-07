import json
from logging import getLogger
from pathlib import Path
from queue import Empty, Queue
from shutil import which
from subprocess import DEVNULL, PIPE, Popen, run
from threading import Event, Thread
from time import sleep, time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

from .resources import LogMessage, Request

logger = getLogger(__name__)


class WaitForFileCreationHandler(FileSystemEventHandler):
    """Event handler that stops an observer when a specific file is created."""

    def __init__(self, observer: Observer, target_file: Path) -> None:
        """Initialize a new WaitForFileCreationHandler instance.

        Parameters
        ----------
        observer (Observer): The observer to stop when the target file is created.
        target_file (Path): The file to watch for creation.
        """
        self.observer = observer
        self.target_file = target_file

    def on_created(self, event):
        """Handle the file creation event."""
        if str(event.src_path) == str(self.target_file):
            logger.info(f"{self.target_file} has been created.")
            self.observer.stop()


class LogFileEventHandler(FileSystemEventHandler):
    """Event handler for processing log files."""

    def __init__(self, callback, target_file: Path) -> None:
        """Initialize a new LogFileEventHandler instance.

        Parameters
        ----------
        callback (callable): The function to call when processing a log line.
        target_file (Path): The log file to watch for changes.
        """
        self.callback = callback
        self.target_file = target_file

    def initial_read(self):
        """Read and process the initial content of the log file."""
        with self.target_file.open() as file:
            content = file.readlines()
            for line in content:
                self.callback(line)

    def on_modified(self, event):
        """Handle the file modification event."""
        if str(event.src_path) == str(self.target_file):
            with Path(event.src_path).open() as file:
                content = file.readlines()
                for line in content[-1:]:
                    self.callback(line)


class MockoonServer:
    """A class for running a Mockoon server instance and interacting with its logs."""

    WAIT_TIMEOUT = 30

    def __init__(
        self,
        data_file: str,
        hostname: str | None = None,
        port: int | None = None,
        pname: str | None = None,
        *,
        use_docker: bool = False,
        repair: bool | None = False,
    ) -> None:
        """Initialize a new MockoonServer instance.

        Parameters
        ----------
        data_file (str): Path to Mockoon data file.
        hostname (str, optional): The hostname to use for the server. Defaults to None.
        port (int, optional): The port to use for the server. Defaults to None.
        pname (str, optional): The process name for the server. Defaults to None.
        use_docker (bool, optional): Whether to use Docker to run the server. Defaults to False.
        repair (bool, optional): Whether to repair the data file before starting the server. Defaults to False.
        """
        if not Path(data_file).exists():
            msg = f"Mockoon server environment data file not found: {data_file}"
            raise Exception(
                msg,
            )

        self.data_file = Path(data_file)

        data = json.load(self.data_file.open())

        if use_docker and not which("docker"):
            msg = "mockoon-cli is not available locally"
            raise Exception(msg)

        if not use_docker and not which("mockoon-cli"):
            msg = "mockoon-cli is not available locally"
            raise Exception(msg)

        self.use_docker = use_docker

        self.hostname = hostname if hostname else data["hostname"]
        self.port = port if port else data["port"]
        self.pname = pname if pname else data["name"].replace(" ", "-").lower()
        self.repair = repair

        self.log_messages: list[LogMessage] = []

        self.log_streaming_thread = None

        self.event_queue: Queue[str] = Queue()
        self.stop_event = Event()

    def __enter__(self):
        """Start the MockoonServer and return the instance when used in a 'with' statement."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Stop the MockoonServer when exiting a 'with' statement."""
        self.stop()

    @property
    def _mockoon_cli_command(self):
        """Construct the mockoon-cli command based on the instance properties.

        Returns
        -------
        list[str]: The mockoon-cli command as a list of strings.
        """
        if self.use_docker:
            command = [
                "docker",
                "run",
                "--name=mockoon-cli",
                "-d",
                "--mount",
                f"type=bind,source={self.data_file.resolve()},target=/data,readonly",
                "-p",
                f"{self.port}:{self.port}",
                "mockoon/cli:latest",
                "--log-transaction",
                "--data",
                "data",
            ]

        else:
            command = [
                "mockoon-cli",
                "start",
                "--log-transaction",
                "--data",
                self.data_file,
            ]

        if self.hostname:
            command += ["--hostname", self.hostname]

        command += ["--pname", self.pname, "--port", str(self.port)]

        command += [
            "--pname",
            self.pname,
            "--hostname",
            self.hostname,
            "--port",
            str(self.port),
        ]

        if self.repair:
            command += ["--repair"]

        return command

    def _stream_logs(self, log_source):
        """Stream the JSON-formatted stdout output of the mockoon-cli process and process the log lines."""
        if not log_source:
            return

        def process_line(line):
            """Process a log line by parsing the JSON-formatted output, updating the log messages, and emitting events for server readiness and transactions on specific routes."""
            log_entry = json.loads(line)

            log_message = LogMessage.from_log_entry(log_entry)

            if transaction := log_message.transaction:
                logger.info("Transaction received")

                # Add 'received request' event for each route
                #   so that tests can wait for logs to be written
                route = transaction.request.route
                self.event_queue.put(route)
            else:
                logger.debug(f"Message from server has no transaction: {log_message}")

            self.log_messages.append(log_message)

            server_start_msg_prefix = "Server started on port "
            message = log_message.message
            if server_start_msg_prefix in message:
                self.event_queue.put("ready")

        if self.use_docker:
            for line in log_source.stdout:
                if self.stop_event.is_set():
                    break
                process_line(line)
        else:
            event_handler = LogFileEventHandler(
                callback=process_line,
                target_file=log_source,
            )
            event_handler.initial_read()
            observer = PollingObserver()
            observer.schedule(event_handler, path=log_source.parent, recursive=False)
            observer.start()

            while not self.stop_event.is_set():
                sleep(0.1)

            observer.stop()
            observer.join()

    def _cleanup(self):
        """Clean up any running mockoon-cli or Docker processes related to the mock server."""
        if which("docker"):
            run(
                ["docker", "stop", "mockoon-cli", "-t", "0"],
                stdout=DEVNULL,
                stderr=DEVNULL,
            )
            run(["docker", "rm", "mockoon-cli"], stdout=DEVNULL, stderr=DEVNULL)

        if which("mockoon-cli"):
            run(
                ["mockoon-cli", "stop", f"mockoon-{self.pname}"],
                stdout=DEVNULL,
                stderr=DEVNULL,
            )

    def _pre_start(self):
        """Perform pre-start operations such as pulling the latest Docker image for Mockoon (if using Docker) or deleting any existing log files."""
        if self.use_docker:
            run(
                ["docker", "pull", "mockoon/cli:latest"],
                stdout=DEVNULL,
                stderr=DEVNULL,
            )

        else:
            Path(
                f"~/.mockoon-cli/logs/mockoon-{self.pname}-out.log",
            ).expanduser().unlink(missing_ok=True)

    def start(self):
        """Start the mock API.

        This method starts the `mockoon-cli` process in a new thread, and streams the JSON-formatted stdout output
        to the `logs` property of the `MockoonServer` instance.
        """
        self.stop()

        self._pre_start()

        run(self._mockoon_cli_command, stdout=DEVNULL, stderr=DEVNULL)

        if self.use_docker:
            log_source = Popen(["docker", "logs", "-f", "mockoon-cli"], stdout=PIPE)
        else:
            target_file = Path(
                f"~/.mockoon-cli/logs/mockoon-{self.pname}-out.log",
            ).expanduser()

            if not target_file.is_file():
                observer = Observer()
                event_handler = WaitForFileCreationHandler(observer, target_file)

                observer.schedule(
                    event_handler,
                    path=target_file.parent,
                    recursive=False,
                )
                observer.start()

                timeout = 60  # Timeout in seconds
                start_time = time()

                try:
                    while observer.is_alive() and time() - start_time < timeout:
                        observer.join(timeout=1)
                except Exception as e:
                    logger.info(f"Error: {e}")
                finally:
                    observer.stop()
                observer.join()

                if time() - start_time >= timeout:
                    msg = "Timeout reached. Server log file not created"
                    raise Exception(msg)

            log_source = target_file

        self.log_streaming_thread = Thread(
            target=self._stream_logs,
            args=[log_source],
        )
        self.log_streaming_thread.start()

        # Wait for server to start
        self.wait_for_active()

    def _wait_for_event(self, expected_event, timeout=None):
        wait_timeout = self.WAIT_TIMEOUT if timeout is None else timeout

        start_time = time()
        timeout_time = start_time + wait_timeout

        while True:
            if not self.log_streaming_thread.is_alive():
                msg = "Server thread is not alive."
                raise Exception(msg)

            if time() > timeout_time:
                msg = f"Server did not start within {wait_timeout} seconds."
                raise Exception(msg)

            event = None
            try:
                remaining_timeout_time = timeout_time - time()
                event = self.event_queue.get(timeout=remaining_timeout_time)
            except Empty:
                pass

            if event == expected_event:
                return

    def wait_for_active(self):
        """Waits for the mock server to be active.

        This method waits for the `mockoon-cli` process started in `start`, if available.
        """
        self._wait_for_event("ready")

    def wait_for_route_hit(self, route: str):
        """Wait for the mock server to be have written logs about a transaction on a particular route."""
        self._wait_for_event(f"/{route}")

    def stop(self):
        """Stop the mock API.

        This method terminates the mockoon-cli process and waits for the streaming thread to complete.
        """
        self._cleanup()

        if self.log_streaming_thread:
            self.stop_event.set()
            self.log_streaming_thread.join()

    @property
    def root_uri(self):
        return f"http://localhost:{self.port}"

    @property
    def transactions(self):
        """Return transactions from log messages that contained them."""
        return [
            log.transaction for log in self.log_messages if log.transaction is not None
        ]

    def reset_transactions(self):
        """Reset the transactions list."""
        self.log_messages = []

    @property
    def call_count(self):
        """Return the number of calls to the mock server."""
        return len(self.transactions)

    @property
    def called(self):
        """Return True if the mock server was called at least once, False otherwise."""
        return bool(self.transactions)

    @property
    def call_request(self):
        """Return the last request to the mock server."""
        return self.transactions[-1].request if self.transactions else None

    @property
    def call_requests_list(self):
        """Return the list of requests to the mock server."""
        return [t.request for t in self.transactions]

    def assert_not_called(self):
        """Assert the mock server was never called."""
        assert not self.called

    def assert_called(self):
        """Assert the mock server was called at least once."""
        assert self.called

    def assert_called_once(self):
        """Assert the mock server was called exactly once."""
        assert self.call_count == 1

    def _get_no_of_calls_with_request(self, request):
        """Return the number of calls that the server has that matches a request."""
        return self.call_requests_list.count(request)

    def assert_called_once_with(self, request):
        """Assert the mock server was called exactly once with the specified arguments."""
        assert self._get_no_of_calls_with_request(request) == 1

    def assert_called_with(self, request):
        """Assert the mock server was last called with the specified arguments."""
        assert self._get_no_of_calls_with_request(request) > 0

    def assert_has_calls(self, requests: list[Request], *, any_order=False):
        """Assert the mock server has been called with the specified calls."""
        if any_order:
            remaining_requests = self.call_requests_list.copy()
            for request in requests:
                if request in remaining_requests:
                    remaining_requests.remove(request)
                else:
                    msg = f"Expected call not found: {request}"
                    raise AssertionError(msg)
        else:
            matched_request_count = 0
            for actual_request in self.call_requests_list:
                if requests[matched_request_count] == actual_request:
                    matched_request_count += 1
                    if matched_request_count == len(requests):
                        break

            if matched_request_count != len(requests):
                msg = f"Expected calls {requests} not found in the same order in {self.call_requests_list}"
                raise AssertionError(
                    msg,
                )

    def _request_matches(self, actual_request, **kwargs):
        """Check if the actual request matches the specified properties."""
        for key, value in kwargs.items():
            if (
                not hasattr(actual_request, key)
                or getattr(actual_request, key) != value
            ):
                return False
        return True

    def _get_no_of_calls_with_properties(self, **kwargs):
        """Return the number of calls that the server has that matches the specified properties."""
        return sum(
            1
            for request in self.call_requests_list
            if self._request_matches(request, **kwargs)
        )

    def assert_called_once_with_properties(self, **kwargs):
        """Assert the mock server was called exactly once with the specified properties."""
        assert self._get_no_of_calls_with_properties(**kwargs) == 1

    def assert_called_with_properties(self, **kwargs):
        """Assert the mock server was last called with the specified properties."""
        assert self._get_no_of_calls_with_properties(**kwargs) > 0

    def assert_has_calls_with_properties(self, calls, *, any_order=False):
        """Assert the mock server has been called with the specified calls, each containing the specified properties."""
        if any_order:
            remaining_requests = self.call_requests_list.copy()
            for call in calls:
                matching_request = next(
                    (
                        request
                        for request in remaining_requests
                        if self._request_matches(request, **call)
                    ),
                    None,
                )
                if matching_request:
                    remaining_requests.remove(matching_request)
                else:
                    msg = f"Expected call not found: {call}"
                    raise AssertionError(msg)
        else:
            matched_call_count = 0
            for actual_request in self.call_requests_list:
                if self._request_matches(actual_request, **calls[matched_call_count]):
                    matched_call_count += 1
                    if matched_call_count == len(calls):
                        break

            if matched_call_count != len(calls):
                msg = f"Expected calls {calls} not found in the same order in {self.call_requests_list}"
                raise AssertionError(
                    msg,
                )

# CircuitPython Program Templates

## Overview

This repository contains a collection of starter templates for CircuitPython projects designed to help you quickly bootstrap new applications. Templates cover a variety of use cases and functionality from asynchronous task management to network connectivity, NTP time synchronization, syslog logging, and memory monitoring - all tailored for resource-constrained devices.

Each template is thoroughly documented and comes with preconfigured settings via a `settings.toml` file.

## Templates Included

- **Asyncio Program Template:**  
  A robust asynchronous framework featuring:
  - Conditional Wi-Fi connectivity
  - Time synchronization using NTP with hybrid DST support (USA and non-USA)
  - Dual logging (console and optional remote syslog with additional library)
  - Memory monitoring
  - Modular configuration via `settings.toml`

### `asyncio` Program Template Details

#### Key Features

- **Modular & Configurable:**  
  Easily enable/disable features (Wi-Fi, NTP, syslog, etc.) by editing `settings.toml`.
  
- **Asynchronous Operation:**  
  Leverage Python's `asyncio` to run multiple concurrent tasks without blocking, making it straightforward to add new functionality without disturbing existing code.

- **Common Features Pre-Integrated:**  
  Wi-Fi, NTP time synchronization, logging, and more are already implemented so it's east to just jump right in and add new tasks for your own functionality.

- **Dynamic Library Loading:**  
  If you don't need Wi-Fi, disable it in the `settings.toml` file and the library won't even load. The same thing goes for all of the optional functionality in the template.
  
- **Thorough Documentation:**  
  Both the code and configuration files include detailed comments to help you understand and customize each part of the template.
  
- **Tested Platforms:**  
  The code has been tested on:
  - **Raspberry Pi Pico W (RP2040)**
  - **Raspberry Pi Pico 2 W (RP2350)**
  
- **Open Source:**  
  Distributed under the GPL-3.0 License.

#### Minimum Required Libraries

For this template to run correctly, please ensure that the following libraries are installed in the `lib` directory or present in the firmware build (some of these are included in the official CircuitPython bundle):

- **Standard Libraries (built-in):**
  - `os` (used for reading the settings.toml file)
  - `gc` (garbage collection)
  - `asyncio` (run multiple tasks concurrently)
  - `time` (for handling time)
  - `wifi` (connect to wireless networks)  
  - `socketpool` (network socket management)
  
- **Additional CircuitPython Libraries:**
  - **Time Synchronization:**  
    - `adafruit_ntp` (used for synchronizing time via NTP)
  - **(Optional) Remote Logging:**  
    - A syslog client library (e.g., [`usyslog`](https://github.com/ageagainstthemachine/circuitpython-usyslog)) if you wish to enable remote syslog logging.

*Note:* Some of these libraries are available as part of the [CircuitPython Bundle](https://circuitpython.org/libraries) provided by Adafruit. Make sure you are using a version of CircuitPython that supports `asyncio` (v9.x or later is recommended).

#### Getting Started

1. **Clone the Repository:**
    - bash: git clone, etc.

2. **Copy Files to Your Board:**
   - Copy the template's `code.py` to the root directory of your board.
   - Copy the accompanying `settings.toml` file to your board as well.

3. **Configure Settings:**
   - Open `settings.toml` and adjust the parameters (e.g., Wi-Fi SSID/PSK, NTP settings) to suit your environment and use case.

4. **Run the Program:**
   - Once the files are in place, the program will do the following things:
     - Attempt to connect to Wi-Fi (if enabled)
     - Synchronize time using NTP (with optional DST adjustments and server configurability)
     - Start the main asynchronous tasks (including a dummy task for demonstration)

#### Code Structure & Documentation

##### Code Overview

- **Configuration Class:**  
  Loads settings from `settings.toml` and converts them into easy-to-access environment variables.
  
- **Logging & Diagnostics:**  
  The `structured_log()` function provides uniform logging to the console and (optionally) a remote syslog server. Memory usage is periodically monitored using `monitor_memory()`. Note: syslog functionality requires a separate library (e.g., [`usyslog`](https://github.com/ageagainstthemachine/circuitpython-usyslog)).

- **Network Connectivity:**  
  Contains both a synchronous Wi-Fi connection function and an asynchronous task that continuously monitors and re-establishes connectivity.

- **Time Synchronization:**  
  Utilizes `adafruit_ntp` for fetching the current UTC time, applies the base timezone offset, and dynamically (or statically) adjusts for DST.

- **Task Management:**  
  Demonstrates how to structure asynchronous tasks using `asyncio`. The `dummy_task()` serves as an example of a periodic task.

##### Adding New Tasks

To add a new asynchronous task:

1. **Define Your Task:**  
   Create an async function (note: see the `dummy_task()` for an example) to encapsulate your new functionality.

2. **Integrate with the Main Loop:**  
   In the `main()` function, add your new task to the tasks list:
   ```python
   tasks.append(asyncio.create_task(your_new_task()))
   ```

3. **Logging & Error Handling:**  
   Use `structured_log()` to record key events and errors in a unified manner. Optionally, incorporate memory monitoring during critical operations using `monitor_memory()`.

#### Configuration Settings

Below is a detailed explanation of the configurable settings available in `settings.toml`:

##### Network Configuration

- **WIFI_ENABLED**  
  *Value:* `"TRUE"` or `"FALSE"`  
  *Description:* Enables or disables Wi-Fi connectivity. When enabled, the program will attempt to connect using the provided SSID and PSK.

- **SSID**  
  *Value:* Your Wi-Fi network's SSID (e.g., `"Your_SSID"`)  
  *Description:* The identifier for your Wi-Fi network. Note that this is required when `WIFI_ENABLED` is set to `"TRUE"`.

- **PSK**  
  *Value:* Your Wi-Fi network password (e.g., `"Your_PSK"`)  
  *Description:* The pre-shared key (password) required to connect to your Wi-Fi network.

##### NTP (Time Synchronization) Configuration

- **NTP_ENABLED**  
  *Value:* `"TRUE"` or `"FALSE"`  
  *Description:* Enables or disables the NTP time synchronization task. When enabled, the program fetches the current time from an NTP server.

- **NTP_OFFSET**  
  *Value:* A numerical value representing the timezone offset in hours (e.g., `"-8"`)  
  *Description:* The base timezone offset to be applied to UTC time.

- **NTP_SYNC_INTERVAL**  
  *Value:* A numerical value indicating the interval (in seconds) for synchronizing time (e.g., `"3600"`)  
  *Description:* Determines how frequently the NTP sync task updates the time.

##### DST (Daylight Savings Time) Configuration

- **DST_ENABLED**  
  *Value:* `"TRUE"` or `"FALSE"`  
  *Description:* Enables or disables DST adjustments. When disabled, DST corrections are not applied, and `is_dst()` always returns `False`.

- **DST_MODE**  
  *Value:* `"dynamic"` or `"static"`  
  *Description:*  
  - **Dynamic:** Computes DST boundaries based on U.S. rules (second Sunday in March to the first Sunday in November).  
  - **Static:** Uses the provided `DST_START` and `DST_END` values.

- **DST_OFFSET**  
  *Value:* An integer representing the additional hour offset during DST (e.g., `1`)  
  *Description:* The extra offset applied during DST.

- **DST_START**  
  *Value:* A string in the format `"MM-DD HH:MM"` (e.g., `"03-14 02:00"`)  
  *Description:* The static start time for DST (used if `DST_MODE` is not set to `"dynamic"`).

- **DST_END**  
  *Value:* A string in the format `"MM-DD HH:MM"` (e.g., `"11-07 02:00"`)  
  *Description:* The static end time for DST (used if `DST_MODE` is not set to `"dynamic"`).

- **NTP_SERVER**  
  *Value:* A string representing the NTP server address (leave empty for library-included default, e.g., `"pool.ntp.org"`)  
  *Description:* Specifies a custom NTP server for time synchronization.

##### Syslog & Diagnostics Configuration

- **SYSLOG_SERVER_ENABLED**  
  *Value:* `"TRUE"` or `"FALSE"`  
  *Description:* Enables or disables remote syslog logging. When enabled, logs are sent to the specified syslog server.

- **SYSLOG_SERVER**  
  *Value:* A string containing the syslog server address (e.g., `"10.0.0.10"`)  
  *Description:* The IP address or hostname of the syslog server.

- **SYSLOG_PORT**  
  *Value:* A numerical value indicating the port (e.g., `"514"`)  
  *Description:* The port number to be used for syslog communication.

- **MEMORY_MONITORING**  
  *Value:* `"TRUE"` or `"FALSE"`  
  *Description:* When enabled, the program periodically logs memory usage details for diagnostic purposes.

- **CONSOLE_LOG_ENABLED**  
  *Value:* `"TRUE"` or `"FALSE"`  
  *Description:* When enabled, log messages are output to the console. This is useful for real-time debugging and troubleshooting.

#### Troubleshooting

If you encounter issues while running the template, consider the following checks:

- **Wi-Fi Connectivity:**  
  - Ensure that `WIFI_ENABLED` is set to `"TRUE"` in `settings.toml`.  
  - Verify that `SSID` and `PSK` are correctly configured for your network.
  
- **Time Synchronization Issues:**  
  - Confirm that `NTP_ENABLED` is `"TRUE"` and `NTP_SERVER` is either left empty (to use the default) or set to a reachable server.  
  - Check that `NTP_OFFSET` and `NTP_SYNC_INTERVAL` are correctly set for your timezone and desired update frequency.
  - If you're using DST adjustments, verify that `DST_ENABLED` is `"TRUE"` and that `DST_MODE`, `DST_OFFSET`, `DST_START`, and `DST_END` reflect your preferred DST configuration.

- **Logging & Diagnostics:**  
  - If no logs appear on your console, ensure `CONSOLE_LOG_ENABLED` is `"TRUE"`.  
  - For remote logging issues, verify that `SYSLOG_SERVER_ENABLED` is `"TRUE"` and that the `SYSLOG_SERVER` and `SYSLOG_PORT` values are correct, as well as the library is present on your board in the lib folder.
  - Enable `MEMORY_MONITORING` and console logging if you suspect resource constraints might be affecting performance or functionality.

- **General Debugging:**  
  - Review the comments in both `code.py` and `settings.toml` for guidance on how each setting affects program behavior.
  - Ensure that your CircuitPython version is compatible (v9.x or later is recommended).

---

#### FAQ

TBD

#### Known Issues

- The circuitpython-usyslog support needs to be implemented better (handle log severity levels more explicitly).

#### Fixed Issues

- WiFi connection errors result in unhandled exception - fixed in [this commit](https://github.com/ageagainstthemachine/CircuitPython-Program-Templates/commit/5e79f58c31436721180801bdbc912d5492274718).

#### Contributing

Contributions are encouraged. If you have improvements, additional templates, or new features, please submit a pull request. When contributing, please abide by the following:

- Follow the established code style and commenting conventions.
- Update the documentation where necessary.
- Ensure compatibility with the tested platforms.

Note: If you successfully test this on a board/platform other than the RPi Pico W and 2 W, please let me know!

#### License

This project is licensed under the **GPL-3.0 License**. See the [LICENSE](LICENSE) file for further details.

#### Disclaimer

This project is provided "as-is" without any warranties. Like everything else on the internet, use at your own risk.

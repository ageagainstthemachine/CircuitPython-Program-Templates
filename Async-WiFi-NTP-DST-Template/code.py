# CircuitPython Template Program 20250417a
# https://github.com/ageagainstthemachine/CircuitPython-Program-Templates
#
# This template demonstrates how to:
#   1) Conditionally connect to Wi-Fi
#   2) Synchronize time with an NTP server using a hybrid DST approach
#   3) Log messages both to the console and (optionally) to a remote Syslog server
#
# The template uses a central "Config" class to load configuration values from
# settings.toml. Each section is thoroughly commented to aid in understanding.

################################################################################
#  Libraries & Modules
################################################################################
import os            # Used to read environment variables (from settings.toml)
import gc            # Garbage collection module (for memory monitoring)
import asyncio       # Asynchronous programming library for tasks
import rtc           # For the internal RTC
import time          # Ensure time functions are available

################################################################################
#  Configuration Class
################################################################################
class Config:
    """
    The Config class reads environment variables from settings.toml and stores them
    as class attributes for easy access throughout the program.
    """
    
    # Network & Logging Flags (convert strings to booleans)
    WIFI_ENABLED = os.getenv("WIFI_ENABLED", "false").lower() == "true" # Enable or disable Wi-Fi (disabled by default if unset)
    NTP_ENABLED = os.getenv("NTP_ENABLED", "false").lower() == "true" # Enable or disable NTP support (disabled by default if unset)
    SYSLOG_SERVER_ENABLED = os.getenv("SYSLOG_SERVER_ENABLED", "false").lower() == "true" # Enable or disable syslog (disabled by default if unset)
    MEMORY_MONITORING = os.getenv("MEMORY_MONITORING", "false").lower() == "true" # Enable or disable memory monitoring (disabled by default if unset)
    CONSOLE_LOG_ENABLED = os.getenv("CONSOLE_LOG_ENABLED", "false").lower() == "true" # Enable or disable console logging (disabled by default if unset)
    DEVICE_HOSTNAME = os.getenv("DEVICE_HOSTNAME", "") # Device hostname (currently only used for syslog functionality, but possibly more in the future)

    # WiFi Configuration: SSID and PSK for connecting to a Wi-Fi network
    SSID = os.getenv("SSID", "") # SSID (network name)
    PSK = os.getenv("PSK", "") # PSK (pre-shared key AKA password)

    # Syslog Configuration: Remote server details for syslog logging (if used) - Note: Only usyslog-circuitpython is currently supported by this framework
    SYSLOG_SERVER = os.getenv("SYSLOG_SERVER", "") # Syslog server target (URL or IP)
    SYSLOG_PORT = int(os.getenv("SYSLOG_PORT", 514)) # Syslog server port
    SYSLOG_TIMESTAMP_ENABLED = os.getenv("SYSLOG_TIMESTAMP_ENABLED", "true").lower() == "true" # Syslog timestamp enabled

    # NTP Configuration: Parameters to synchronize time from an NTP server
    DEFAULT_NTP_OFFSET = -8 # Default timezone offset (in hours)
    DEFAULT_NTP_SYNC_INTERVAL = 3600 # Default NTP sync interval (in seconds) to resync time
    NTP_OFFSET = int(os.getenv("NTP_OFFSET", DEFAULT_NTP_OFFSET))    # Timezone offset (in hours)
    NTP_SYNC_INTERVAL = int(os.getenv("NTP_SYNC_INTERVAL", DEFAULT_NTP_SYNC_INTERVAL))  # NTP sync interval (in seconds) to resync time
    NTP_SERVER = os.getenv("NTP_SERVER", "")  # NTP server address - if empty, the NTP library default is used

    # DST (Daylight Savings Time) Configuration: Controls how DST adjustments are applied
    DST_ENABLED = os.getenv("DST_ENABLED", "false").lower() == "true"
    DST_MODE = os.getenv("DST_MODE", "dynamic")  # "dynamic" uses computed boundaries (US); "static" uses provided dates (non-US)
    DST_OFFSET = int(os.getenv("DST_OFFSET", 1))   # Additional offset during DST (typically +1 hour)
    DST_START = os.getenv("DST_START", "03-14 02:00")  # Static DST start time (used if DST_MODE is "static")
    DST_END = os.getenv("DST_END", "11-07 02:00")    # Static DST end time (used if DST_MODE is "static")

################################################################################
#  Logging & Memory Monitoring Setup
################################################################################

# Global variable for a syslog client (if syslog is enabled and configured)
syslog_client = None  

def structured_log(message, level=6, tag=None):
    """
    Logs a message to the console (if enabled via configuration) and optionally
    sends the message to a remote Syslog server if a syslog client is set up.
    """
    # Log to console if enabled.
    if Config.CONSOLE_LOG_ENABLED:
        print(message)
    
    # If a syslog client is available, try to send the message.
    if syslog_client:
        try:
            syslog_client.log(level, message, tag)
        except RuntimeError:
            pass  # Ignore errors due to transient network issues


def monitor_memory(mem_tag=""):
    """
    Logs current memory usage information. This can be useful to diagnose
    memory-related issues on resource-constrained devices.
    """
    if Config.MEMORY_MONITORING:
        gc.collect()  # Trigger garbage collection to free up memory
        free_mem = gc.mem_free()      # Get amount of free memory
        used_mem = gc.mem_alloc()     # Get amount of allocated memory
        total_mem = free_mem + used_mem
        free_pct = (100 * free_mem / total_mem) if total_mem > 0 else 0
        used_pct = (100 * used_mem / total_mem) if total_mem > 0 else 0

        # Build a detailed memory usage log message
        structured_log("[Memory] " + mem_tag + " - Free=" + str(free_mem) + " (" + "{:.2f}".format(free_pct) + "%), Used=" + str(used_mem) + " (" + "{:.2f}".format(used_pct) + "%), Total=" + str(total_mem), tag="memory_status")

################################################################################
#  Conditional Wi-Fi Setup
################################################################################

if Config.WIFI_ENABLED:
    import wifi            # CircuitPython Wi-Fi library
    import socketpool      # Provides a socket pool for network operations

    # Create a socket pool using the current Wi-Fi radio
    pool = socketpool.SocketPool(wifi.radio)

    # Conditionally import and initialize usyslog client
    if Config.SYSLOG_SERVER_ENABLED:
        import usyslog

        # Instantiate syslog client using socketpool and Config values
        syslog_client = usyslog.UDPClient(
            pool=pool, # Use the previously-created pool
            ip=Config.SYSLOG_SERVER, # Desired server (set in settings.toml file)
            port=Config.SYSLOG_PORT, # Desired port (set in settings.toml file)
            tag=None,  # Tag for better RFC compliance where the default tag is None, but can be overridden in each log call
            hostname=Config.DEVICE_HOSTNAME if Config.DEVICE_HOSTNAME else None, # Hostname for better RFC compliance (set in settings.toml if desired)
            include_timestamp=Config.SYSLOG_TIMESTAMP_ENABLED # Timestamp enable/disable for better RFC compliance (set in settings.toml if desired)
        )

    def wifi_connect_sync():
        """
        Attempts to connect to the Wi-Fi network using credentials provided in Config.
        This is a one-time synchronous attempt.
        """
        if not wifi.radio.connected:
            try:
                wifi.radio.connect(Config.SSID, Config.PSK)
                structured_log("Wi-Fi connected: " + str(wifi.radio.ipv4_address), tag="wifi_connect")
            except ConnectionError as e:
                structured_log("Wi-Fi connection failed: " + str(e), tag="wifi_connect")

    async def wifi_connect_task():
        """
        Asynchronous task that continuously checks Wi-Fi connectivity.
        If the device becomes disconnected, it attempts to reconnect every 10 seconds.
        """
        while True:
            if not wifi.radio.connected:
                try:
                    wifi.radio.connect(Config.SSID, Config.PSK)
                    structured_log("Wi-Fi reconnected: " + str(wifi.radio.ipv4_address), tag="wifi_connect")
                except ConnectionError as e:
                    structured_log("Wi-Fi reconnection failed: " + str(e), tag="wifi_connect")
                    monitor_memory("During Wi-Fi reconnect")
                    await asyncio.sleep(10)  # Wait 10 seconds before trying again
            else:
                await asyncio.sleep(60)  # Check connectivity every 60 seconds
else:
    # Define empty functions if Wi-Fi is disabled in the configuration
    def wifi_connect_sync(): pass
    async def wifi_connect_task(): pass

################################################################################
#  Conditional NTP Setup with Hybrid DST (US & Non-US) and Configurable Server
################################################################################

# Global flag to track if time synchronization was successful
time_synced = False  

# Check if DST adjustments are enabled in the configuration
if Config.DST_ENABLED:

    def adjust_utc_time(utc_time, offset):
        """
        Adjusts a given UTC time (struct_time) by a specified offset (in hours).
        This function creates a new time tuple with the hour modified by the offset,
        then uses mktime() and localtime() to correctly normalize the time (handling day rollovers, etc.).
        """
        adjusted = (
            utc_time.tm_year,
            utc_time.tm_mon,
            utc_time.tm_mday,
            utc_time.tm_hour + offset,  # Apply the hour offset here
            utc_time.tm_min,
            utc_time.tm_sec,
            utc_time.tm_wday,
            utc_time.tm_yday,
            utc_time.tm_isdst
        )
        # mktime converts the tuple to seconds since the epoch; localtime converts back to a normalized struct_time
        return time.localtime(time.mktime(adjusted))

    def weekday(year, month, day):
        """
        Returns the weekday (0=Monday, 6=Sunday) for a given date.
        Uses mktime and localtime to compute the weekday.
        """
        return time.localtime(time.mktime((year, month, day, 0, 0, 0, 0, 0, -1))).tm_wday

    def nth_weekday(year, month, weekday_target, n):
        """
        Computes the day number (date) of the nth occurrence of a specified weekday in a month.
        For example, to find the second Sunday in March (weekday_target=6, n=2).
        """
        count = 0
        for day in range(1, 32):  # Loop through possible days (1 to 31)
            try:
                if weekday(year, month, day) == weekday_target:
                    count += 1
                    if count == n:
                        return day
            except Exception:
                break  # Break the loop if an invalid date is reached
        return None

    def get_dynamic_dst_bounds(year):
        """
        Calculates DST boundaries dynamically based on U.S. rules:
          - DST starts on the second Sunday in March at 2:00 AM.
          - DST ends on the first Sunday in November at 2:00 AM.
        Returns a tuple of two struct_time objects representing the start and end times.
        """
        dst_start_day = nth_weekday(year, 3, 6, 2)  # Second Sunday in March (weekday 6 = Sunday)
        dst_end_day   = nth_weekday(year, 11, 6, 1)  # First Sunday in November

        # Create tuples representing the DST start and end times
        dst_start_tuple = (year, 3, dst_start_day, 2, 0, 0, 0, 0, -1)
        dst_end_tuple   = (year, 11, dst_end_day, 2, 0, 0, 0, 0, -1)
        # Normalize these times to ensure correctness
        dst_start = time.localtime(time.mktime(dst_start_tuple))
        dst_end   = time.localtime(time.mktime(dst_end_tuple))
        return dst_start, dst_end

    def parse_static_dst_time(dst_str, year):
        """
        Parses a DST time string in the format 'MM-DD HH:MM' and returns a tuple
        representing that time for a specific year.
        This is used when DST_MODE is set to "static".
        """
        month_day, hm = dst_str.split(" ")
        month, day = map(int, month_day.split("-"))
        hour, minute = map(int, hm.split(":"))
        return (year, month, day, hour, minute, 0, 0, 0, -1)

    def is_dst(utc_time):
        """
        Determines whether Daylight Savings Time (DST) is in effect.
        It converts the provided UTC time to local standard time by applying the base NTP_OFFSET,
        then checks whether that local time falls within the DST period, either computed dynamically
        or parsed from static configuration values.
        """
        # Convert raw UTC to local standard time using the base offset from Config
        local_standard = adjust_utc_time(utc_time, Config.NTP_OFFSET)
        year = local_standard.tm_year

        # Choose DST calculation method based on the DST_MODE setting
        if Config.DST_MODE.lower() == "dynamic":
            dst_start, dst_end = get_dynamic_dst_bounds(year)
        else:
            # Parse static DST start and end times from configuration
            dst_start = time.localtime(time.mktime(parse_static_dst_time(Config.DST_START, year)))
            dst_end   = time.localtime(time.mktime(parse_static_dst_time(Config.DST_END, year)))
        # Return True if the current local standard time is within the DST period
        return dst_start <= local_standard < dst_end
else:
    # If DST adjustments are disabled, this function always returns False
    def is_dst(utc_time):
        return False

# Set up the NTP section only if NTP is enabled in the configuration
if Config.NTP_ENABLED:
    import adafruit_ntp   # Library to handle NTP synchronization

    async def ntp_time_sync_task():
        """
        Periodically fetches the current time from an NTP server and adjusts it based on
        the configured time zone and DST settings. The adjusted local time is then logged.
        """
        global time_synced

        structured_log("NTP: Initializing client...", tag="ntp_sync")
        try:
            # Initialize the NTP client using a raw UTC mode (tz_offset=0)
            # If a custom NTP_SERVER is specified in the configuration, use it instead of the default
            if Config.NTP_SERVER:
                ntp = adafruit_ntp.NTP(pool, server=Config.NTP_SERVER, tz_offset=0)
            else:
                ntp = adafruit_ntp.NTP(pool, tz_offset=0)
            structured_log("NTP: Client initialized.", tag="ntp_sync")
        except Exception as e:
            # Log any errors that occur during NTP client creation
            structured_log("NTP: Error creating client: " + str(e), tag="ntp_sync")
            return

        r = rtc.RTC()  # Prepare an RTC object for setting system time

        # Enter a loop to periodically sync time.
        while True:
            try:
                structured_log("NTP: Fetching time...", tag="ntp_sync")
                # Retrieve raw UTC time from the NTP server
                utc_time = ntp.datetime

                # Check for valid time data
                if utc_time is None or None in [utc_time.tm_year, utc_time.tm_mon, utc_time.tm_mday,
                                                 utc_time.tm_hour, utc_time.tm_min, utc_time.tm_sec]:
                    structured_log("NTP: Invalid response received: " + str(utc_time), tag="ntp_sync")
                else:
                    # Start with the base timezone offset
                    effective_offset = Config.NTP_OFFSET
                    # Add the DST offset if DST is determined to be active
                    if is_dst(utc_time):
                        effective_offset += Config.DST_OFFSET

                    # Adjust the raw UTC time by the effective offset to obtain local time
                    local_time = adjust_utc_time(utc_time, effective_offset)

                    # Format the local time as a string using .format() for compatibility
                    formatted_time = "{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                        local_time.tm_year,
                        local_time.tm_mon,
                        local_time.tm_mday,
                        local_time.tm_hour,
                        local_time.tm_min,
                        local_time.tm_sec
                    )
                    # Log the synchronized local time and the effective offset used
                    structured_log("NTP: Time synced successfully: " + formatted_time + " (UTC offset: " + str(effective_offset) + ")", tag="ntp_sync")
                    # Set time_synced to true since it was successful
                    time_synced = True
                    # Set the RTC so time.localtime() is actually correct
                    r.datetime = local_time  # local_time is a time.struct_time

            except Exception as e:
                # Log any errors encountered during time synchronization
                structured_log("NTP: Error syncing time: " + str(e), tag="ntp_sync")

            # Monitor and log memory usage after each sync attempt
            monitor_memory("After NTP sync")
            # Wait for the configured sync interval before trying again
            await asyncio.sleep(Config.NTP_SYNC_INTERVAL)
else:
    # Define a placeholder function if NTP is disabled
    async def ntp_time_sync_task():
        """Placeholder function when NTP is disabled to avoid syntax errors."""
        return

################################################################################
#  Example Dummy Task
################################################################################

async def dummy_task():
    """
    A simple asynchronous task that logs a message and memory stats every 10 seconds.
    This is useful for testing and ensuring the event loop remains active.
    """
    while True:
        structured_log("Hello from dummy_task!", tag="dummy_task")
        monitor_memory("dummy_task")
        await asyncio.sleep(10)

################################################################################
#  main() - Gather & Run Tasks
################################################################################

async def main():
    """
    The main coroutine that sets up and runs all enabled tasks.
    It starts Wi-Fi, NTP, and the dummy task, then gathers them with asyncio.
    """
    # Synchronously attempt Wi-Fi connection first
    if Config.WIFI_ENABLED:
        wifi_connect_sync()

    tasks = []

    # If Wi-Fi is enabled, add the asynchronous Wi-Fi monitoring task
    if Config.WIFI_ENABLED:
        tasks.append(asyncio.create_task(wifi_connect_task()))
    # If NTP is enabled, add the NTP synchronization task
    if Config.NTP_ENABLED:
        tasks.append(asyncio.create_task(ntp_time_sync_task()))

    # Always add the dummy task
    tasks.append(asyncio.create_task(dummy_task()))

    if tasks:
        try:
            # Run all tasks concurrently
            await asyncio.gather(*tasks)
        except Exception as e:
            structured_log("Main task error: " + str(e), tag="main_error")
    else:
        structured_log("No tasks to run. Exiting...", tag="main_error")

# Start the asyncio event loop & catch any exceptions
try:
    asyncio.run(main())
except Exception as e:
    structured_log("Fatal error in asyncio loop: " + str(e), tag="main_error")

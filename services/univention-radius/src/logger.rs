use log::{Level, Log, Metadata, Record, SetLoggerError};
use once_cell::sync::OnceCell;
use std::fs::{File, OpenOptions};
use std::io::Write;
use std::sync::Mutex;

#[repr(u8)]
pub enum DebugLevel {
    Error = 0,
    Warning = 1,
    Process = 2,
    Info = 3,
    Debug = 4,
    Trace = 5,
}

impl DebugLevel {
    pub fn from_int(val: i32) -> Self {
        match val {
            0 => DebugLevel::Error,
            1 => DebugLevel::Warning,
            2 => DebugLevel::Process,
            3 => DebugLevel::Info,
            4 => DebugLevel::Debug,
            5 => DebugLevel::Trace,
            _ => DebugLevel::Error,
        }
    }

    fn to_log_level_filter(&self) -> log::LevelFilter {
        match self {
            DebugLevel::Error => log::LevelFilter::Error,
            DebugLevel::Warning => log::LevelFilter::Warn,
            DebugLevel::Process => log::LevelFilter::Warn,
            DebugLevel::Info => log::LevelFilter::Info,
            DebugLevel::Debug => log::LevelFilter::Debug,
            DebugLevel::Trace => log::LevelFilter::Trace,
        }
    }
}

struct UvLogger {
    file: Mutex<Box<dyn Write + Send>>,
}

impl Log for UvLogger {
    fn enabled(&self, _metadata: &Metadata) -> bool {
        true
    }

    fn log(&self, record: &Record) {
        let now = chrono::Local::now().format("%Y-%m-%dT%H:%M:%S%.6f%:z");
        let level = match record.level() {
            Level::Error => "   ERROR",
            Level::Warn => " WARNING",
            Level::Info => "    INFO",
            Level::Debug => "   DEBUG",
            Level::Trace => "   TRACE",
        };
        let msg = format!("{} {} [         -] {}\n", now, level, record.args());
        if let Ok(mut file) = self.file.lock() {
            let _ = file.write_all(msg.as_bytes());
        }
    }

    fn flush(&self) {
        if let Ok(mut file) = self.file.lock() {
            let _ = file.flush();
        }
    }
}

static LOGGER: OnceCell<UvLogger> = OnceCell::new();

pub fn init_with_writer<W: Write + Send + 'static>(writer: W, level: DebugLevel) -> Result<(), log::SetLoggerError> {
    let logger = LOGGER.get_or_init(|| UvLogger {
        file: Mutex::new(Box::new(writer)),
    });
    log::set_logger(logger)?;
    log::set_max_level(level.to_log_level_filter());
    Ok(())
}

pub fn init(logfile: &str, level: DebugLevel) -> Result<(), log::SetLoggerError> {
    let file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(logfile)
        .unwrap_or_else(|_| unsafe { <File as std::os::unix::io::FromRawFd>::from_raw_fd(2) });
    init_with_writer(file, level)
}

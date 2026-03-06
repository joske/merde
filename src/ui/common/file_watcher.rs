#[allow(clippy::wildcard_imports)]
use super::*;

pub struct FileWatcher {
    pub alive: Rc<Cell<bool>>,
    watch_tx: mpsc::Sender<PathBuf>,
}

impl FileWatcher {
    /// Add a new path (file or directory) to the set of watched paths.
    pub fn watch(&self, path: &Path) {
        let _ = self.watch_tx.send(path.to_path_buf());
    }
}

/// Start a file watcher that polls for changes every 500 ms.
///
/// `on_tick(fs_dirty)` is called every 500 ms. `fs_dirty` is `true` when at
/// least one filesystem event arrived since the last tick.  The `filter`
/// callback (called on the watcher thread) can suppress events — return
/// `false` to ignore an event (e.g. events inside `.git/`).
///
/// The returned `FileWatcher::alive` flag should be set to `false` from a
/// `connect_destroy` handler so the poll loop stops.
type EventFilter = Box<dyn Fn(&notify::Event) -> bool + Send>;

pub fn start_file_watcher(
    paths: &[&Path],
    recursive: bool,
    filter: Option<EventFilter>,
    on_tick: impl FnMut(bool) + 'static,
) -> FileWatcher {
    use notify::{RecursiveMode, Watcher};

    let alive = Rc::new(Cell::new(true));
    let (fs_tx, fs_rx) = mpsc::channel::<()>();
    let (watch_tx, watch_rx) = mpsc::channel::<PathBuf>();

    let mode = if recursive {
        RecursiveMode::Recursive
    } else {
        RecursiveMode::NonRecursive
    };

    let watcher = {
        let mut w =
            notify::recommended_watcher(move |res: Result<notify::Event, notify::Error>| {
                if let Ok(event) = res
                    && filter.as_ref().is_none_or(|f| f(&event))
                {
                    let _ = fs_tx.send(());
                }
            })
            .expect("Failed to create file watcher");
        for p in paths {
            w.watch(p, mode).ok();
        }
        w
    };

    let watcher = RefCell::new(watcher);
    let alive2 = alive.clone();
    let mut on_tick = on_tick;
    gtk4::glib::timeout_add_local(Duration::from_millis(500), move || {
        if !alive2.get() {
            return gtk4::glib::ControlFlow::Break;
        }
        // Process requests to watch new paths (e.g. after Save As).
        while let Ok(new_path) = watch_rx.try_recv() {
            watcher.borrow_mut().watch(&new_path, mode).ok();
        }
        let mut fs_dirty = false;
        while fs_rx.try_recv().is_ok() {
            fs_dirty = true;
        }
        on_tick(fs_dirty);
        gtk4::glib::ControlFlow::Continue
    });

    FileWatcher { alive, watch_tx }
}

from cx_Freeze import setup, Executable

# Include additional files
include_files = [
    ("media", "media"),
    ("config", "config")
]

# List of packages to include
packages = [
    "os",
    "json",
    "hashlib",
    "threading",
    "time",
    "tkinter",
    "requests",
    "PIL",
    "urllib",
    "queue"  # Explicitly include the queue module
]

setup(
    name="GameLauncher",
    version="0.2",
    description="EPIC Shard Launcher",
    options={
        "build_exe": {
            "include_files": include_files,
            "packages": packages  # Include the required packages
        }
    },
    executables=[Executable("main.py", target_name="epic-launcher")]  # Specify the output name here
)
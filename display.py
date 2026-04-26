from rich.console import Console
from rich.table import Table

# one console instance used by all functions in this file
console = Console()

def print_snapshot(cpu, ram, disk):
    # create table with a title
    table = Table(title="System Health Snapshot")

    # add columns
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    table.add_column("Status")

    # determine cpu status and color
    if cpu > 90:
        cpu_status = "[red]CRITICAL[/red]"
    elif cpu > 75:
        cpu_status = "[yellow]WARNING[/yellow]"
    else:
        cpu_status = "[green]OK[/green]"

    # determine ram status and color
    if ram.percent > 90:
        ram_status = "[red]CRITICAL[/red]"
    elif ram.percent > 80:
        ram_status = "[yellow]WARNING[/yellow]"
    else:
        ram_status = "[green]OK[/green]"

    # determine disk status and color
    if disk.percent > 90:
        disk_status = "[red]CRITICAL[/red]"
    elif disk.percent > 75:
        disk_status = "[yellow]WARNING[/yellow]"
    else:
        disk_status = "[green]OK[/green]"

    # add one row per metric
    table.add_row("CPU",  f"{cpu}%", cpu_status)
    table.add_row("RAM",  f"{ram.percent}% ({ram.used // (1024**2)} MB)", ram_status)
    table.add_row("Disk", f"{disk.percent}% ({disk.free // (1024**3)} GB free)", disk_status)

    console.print(table)


def print_processes(process_list):
    # create table for processes
    table = Table(title="Top Processes by RAM")

    # add three columns
    table.add_column("Process Name", style="bold")
    table.add_column("PID")
    table.add_column("RAM (MB)", justify="right")

    # loop through every process and add one row each
    for proc in process_list:
        table.add_row(
            proc['name'],
            str(proc['pid']),    # pid is a number, add_row needs strings
            str(proc['ram_mb'])  # ram_mb is a number, convert to string
        )

    console.print(table) 
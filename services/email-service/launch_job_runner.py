import typer
from jobs.job_runner import run

app = typer.Typer()

@app.command()
def launch_worker(
) -> None:
    print(f"Launching worker from typer CLI.")
    run()
    print(f"Returned.")
    typer.Exit(0)

if __name__ == "__main__":
    app()

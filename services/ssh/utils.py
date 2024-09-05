import subprocess


def exec(host: str, user: str, cmd: str) -> tuple[int, list]:
    response = subprocess.run(
        f"ssh {user}@{host} -t '{cmd}'",
        shell=True,
        capture_output=True,
    )

    code = response.returncode

    if code == 0:
        result= response.stdout.decode("utf-8")
    else:
        result= response.stderr.decode("utf-8")
         
    return 0, result


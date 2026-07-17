from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
PROTO = ROOT / "proto" / "inference.proto"


def main():
    command = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{PROTO.parent}",
        f"--python_out={ROOT}",
        f"--grpc_python_out={ROOT}",
        str(PROTO),
    ]
    print("Running:", " ".join(command))
    subprocess.check_call(command)
    print("Generated inference_pb2.py and inference_pb2_grpc.py")


if __name__ == "__main__":
    main()

import re
from dataclasses import dataclass
import argparse
import csv
import os


@dataclass
class UsageInfo:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    send_time: str
    recv_time: str

@dataclass
class PhaseInfo:
    role: str
    phase_name: str
    turn: int
    usage_info: UsageInfo


def parse_log_file(log_file_path):
    # parse the start and end of the 
    phase_infos: list[PhaseInfo] = []
    usage_infos_buffer: list[UsageInfo] = []
    usage_info_buffer: dict[str, int] = {}
    usage_info_recv_read_lines = 0

    with open(log_file_path, 'r') as file:
        for line in file:
            # Check for phase information
            if phase_match := re.search(r'INFO\] (.*?)\: \*\*.*?on : (.*?), turn (\d+)\*\*', line):
                assert len(usage_infos_buffer) > 0, "Usage info buffer is empty"

                role = phase_match.group(1)
                phase_name = phase_match.group(2)
                turn = int(phase_match.group(3))

                # Replace the placeholder with the following code
                phase_infos.append(PhaseInfo(
                    role=role,
                    phase_name=phase_name,
                    turn=turn,
                    usage_info=usage_infos_buffer.pop(0)
                ))

            if phase_match := re.search(r'\[(.*?) INFO\] \*\*\[OpenAI_Usage_Info Send\]\*\*', line):
                send_time = phase_match.group(1)
                assert usage_info_buffer == {}, "Usage info buffer should be empty before sending"
                usage_info_buffer['send_time'] = send_time
                continue

            # Check for OpenAI usage info
            if phase_match := re.search(r'\[(.*?) INFO\] \*\*\[OpenAI_Usage_Info Receive\]\*\*', line):
                assert 'send_time' in usage_info_buffer, "Send time not found in usage info buffer"
                usage_info_buffer['recv_time'] = phase_match.group(1)
                usage_info_recv_read_lines = 3
                continue

            if usage_info_recv_read_lines > 0:
                usage_key_value = re.search(r'(.*?): (\d+)', line)
                assert usage_key_value is not None, "Number not found in line"
                usage_key = usage_key_value.group(1)
                usage_key_value = int(usage_key_value.group(2))
                usage_info_buffer[usage_key] = usage_key_value
                usage_info_recv_read_lines -= 1
                if usage_info_recv_read_lines == 0:
                    usage_infos_buffer.append(UsageInfo(**usage_info_buffer))
                    usage_info_buffer = {}
                continue

    return phase_infos


# Example usage
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process log file and write usage data to an output file.')
    parser.add_argument('input_path', help='Input log file path')
    parser.add_argument('output_path', help='Output file path')
    args = parser.parse_args()

    input_path = args.input_path
    output_path = args.output_path

    usage_data = parse_log_file(input_path)

    if os.path.exists(output_path):
        print(f"Output file {output_path} already exists. Removing it.")
        os.remove(output_path)

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['role', 'phase_name', 'turn', 'prompt_tokens', 'completion_tokens', 'total_tokens', 'send_time', 'recv_time'])
        for entry in usage_data:
            writer.writerow([
                entry.role,
                entry.phase_name,
                entry.turn,
                entry.usage_info.prompt_tokens,
                entry.usage_info.completion_tokens,
                entry.usage_info.total_tokens,
                entry.usage_info.send_time,
                entry.usage_info.recv_time,
            ])
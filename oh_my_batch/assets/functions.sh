GREEN='\033[0;32m'
NC='\033[0m'

checkpoint() {
    local flag_file="$1"
    shift  # Remove the first argument so $@ contains only the command and its arguments
    if [ -f "$flag_file" ]; then
        cat "$flag_file"
    else
        "$@"  # Execute the command
        local exit_code=$?
        if [ $exit_code -eq 0 ]; then
            local current_time=$(date '+%Y-%m-%d %H:%M:%S')
            mkdir -p "$(dirname "$flag_file")"
            printf 'Command succeeded at %s\n' "$current_time" > "$flag_file"
            echo "Created flag file '$flag_file' with timestamp: $current_time"
        else
            echo "Command `$@` failed with exit code $exit_code"
            return $exit_code
        fi
    fi
}

echo -e "${GREEN}Function: checkpoint${NC}"
cat <<EOF
Usage:
    checkpoint <flag_file> <command> [arg1] [arg2] ...

Set a flag file to indicate the completion of a command,
so that it will not be executed again next time.

Example:
    checkpoint lmp.done lmp -in in.lmp

EOF

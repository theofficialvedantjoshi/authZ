import argparse
from vauth.commands import Commands
import time
import os
import keyboard
import cmd
import threading


class VAuthShell(cmd.Cmd):
    """
    vAUTH Shell

    Parameters
    ----------
    cmd : Commands
        Commands object
        user_id : str
        User ID
    """

    intro = r""" 
            $$$$$$\  $$\   $$\ $$$$$$$$\ $$\   $$\ 
           $$  __$$\ $$ |  $$ |\__$$  __|$$ |  $$ |
$$\    $$\ $$ /  $$ |$$ |  $$ |   $$ |   $$ |  $$ |
\$$\  $$  |$$$$$$$$ |$$ |  $$ |   $$ |   $$$$$$$$ |
 \$$\$$  / $$  __$$ |$$ |  $$ |   $$ |   $$  __$$ |
  \$$$  /  $$ |  $$ |$$ |  $$ |   $$ |   $$ |  $$ |
   \$  /   $$ |  $$ |\$$$$$$  |   $$ |   $$ |  $$ |
    \_/    \__|  \__| \______/    \__|   \__|  \__|
                                                   
                                                                                     
Welcome to vAUTH CLI TOOL v1.0. Enter q to quit at any time.
    """
    prompt = "vAUTH> "

    def __init__(self, user_id, key):
        super().__init__()
        self.user_id = user_id
        self.key = key
        self.cmd = Commands()
        self.quit_flag = False

    def check_quit_show_service(self):
        while True:
            if keyboard.is_pressed("q"):
                self.quit_flag = True
                break

    def do_add_service(self, args):
        """
        Add a new service.

        Usage: add_service <service> <username> <seed>
        """
        args = args.split()
        if len(args) != 3:
            print("Usage: add_service <service> <username> <seed>")
            return
        service, username, seed = args
        self.cmd.add_service(self.user_id, self.key, username, service, seed)

    def do_show_service(self, args):
        """
        Display the OTP for a service.

        Usage: show_service <service> <username>
        """
        args = args.split()
        if len(args) != 2:
            print("Usage: show_service <service> <username>")
            return
        service, username = args
        seed = self.cmd.find_seed(self.user_id, self.key, username, service)
        if seed:
            t = threading.Thread(target=self.check_quit_show_service)
            t.start()
            while not self.quit_flag:
                service = self.cmd.show_service(seed, self.user_id, service)
                otp = service[0]
                remaining = int(service[1])
                os.system("cls" if os.name == "nt" else "clear")
                progress = "█" * remaining + "░" * (30 - remaining)
                print(
                    f"Service: {args[0]}\nUsername: {username}\nOTP: {otp}\n{progress} {remaining}s"
                )
                print("Press 'q' to quit")
                if keyboard.is_pressed("q"):
                    break
                time.sleep(1)
                remaining -= 1
                if remaining == 0:
                    remaining = 30
            t.join()

    def do_show_qr(self, args):
        """
        Show the QR code for a service.
        Can be scanned using a TOTP app like Google Authenticator.

        Usage: show_qr <service> <username>
        """
        args = args.split()
        if len(args) != 2:
            print("Usage: show_qr <service> <username>")
            return
        service, username = args
        qr = self.cmd.show_qr(self.user_id, self.key, username, service)
        qr.print_ascii()

    def do_remove_service(self, args):
        """
        Remove a service from the account.

        Usage: remove_service <service> <username>
        """
        args = args.split()
        if len(args) != 2:
            print("Usage: remove_service <service> <username> ")
            return
        service, username = args
        self.cmd.remove_service(self.user_id, username, service)

    def do_modify_service(self, args):
        """
        Modify a service. Can be used to change the username or seed for a service.

        Usage: modify_service <service> <username> <'username'/'seed'> <new_value>
        """
        args = args.split()
        if len(args) != 4:
            print(
                "Usage: modify_service <service> <username> <'username'/'seed'> <new_value>"
            )
            return
        service, username, type, new_value = args
        self.cmd.modify_service(
            self.user_id, self.key, username, service, type, new_value
        )

    def do_q(self, args):
        """
        Quit vAUTH.
        """
        return True

    def default(self, line: str) -> None:
        """
        Default command handler.
        """
        self.stdout.write("x⸑x unknown syntax: %s\n" % line)


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(
        description="vAUTH CLI TOOL",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    register_parser = subparsers.add_parser("register", help="Register a new user")
    register_parser.add_argument("-u", required=True, help="User ID to register")

    login_parser = subparsers.add_parser("login", help="Login to vAUTH")
    login_parser.add_argument(
        "-u",
        required=True,
        help="User ID",
    )

    recover_parser = subparsers.add_parser("recover", help="Recover account")
    recover_parser.add_argument(
        "-u",
        required=True,
        help="User ID",
    )

    remove_parser = subparsers.add_parser("remove", help="Remove account")
    remove_parser.add_argument(
        "-u",
        required=True,
        help="User ID",
    )

    args = parser.parse_args()

    cmd = Commands()

    if args.command == "register":
        recovery_codes = cmd.register(args.u)
        print(f"vAUTH> Registration Successful \nRecovery Codes: {recovery_codes}")
    elif args.command == "login":
        key = cmd.login(args.u)
        shell = VAuthShell(args.u, key)
        shell.cmdloop()
    elif args.command == "recover":
        _key = cmd.recover(args.u)
        print(f"vAUTH> Account recovered successfully")
    elif args.command == "remove":
        cmd.remove_user(args.u)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

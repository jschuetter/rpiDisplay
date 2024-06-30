import cmd

class MyCMD(cmd.Cmd):
    intro = "New CLI"
    prompt = "\\> "

    def do_greet(self, line):
        print("hello, world")

if __name__ == "__main__":
    MyCMD().cmdloop()

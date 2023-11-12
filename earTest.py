from SoxEars.SoxEars import SoxEars


if __name__ == '__main__':
    soxEars  = SoxEars()
    soxEars.startThreadedListening()
    while True:
        cmd = soxEars.getCommand()
        if cmd != "":
            print(cmd)

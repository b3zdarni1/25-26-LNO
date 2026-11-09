f = open('source.bin', 'rb')
d = f.read()
f.close()
open('result.bin', 'wb').write(bytes(255 - b for b in d))
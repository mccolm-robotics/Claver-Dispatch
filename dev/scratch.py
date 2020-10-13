import os
# print(os.urandom(5).hex());

class Test:
    def __init__(self):
        self.my_val = None

    def check(self):
        print("alive!")

    @staticmethod
    def initialize():
        val = "Hello world"
        return val

    def pass_callback(self):
        return Test().initialize

my_test = Test()
val = my_test.pass_callback()
del my_test
new_val = val()
print(new_val)
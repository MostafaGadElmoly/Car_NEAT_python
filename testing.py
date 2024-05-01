#PooP , opject is an instance of a class. 
# opjects is any thing. 
# attribute = is/has 
# Mthod = What can it do? 3.
#__init__ it constract opjects for us 


class Car:




    def __init__(self,make, modle, year, color):
        self.make = make
        self.modle = modle
        self.year  = year 
        self.colour = color

    def drive(self):
        print("this car is going")
        
    def stop(self):
        print("this car stopped")


car_1 = Car("Chevy","CORV",2021,"Blue")

print(car_1.colour)

# class Dog:
#     def __init__(self, name, age):
#         self.name = name
#         self.age = age
#     def get_name(self):
#         return self.name
#     def get_age(self):
#         return self.age
#     def set_age(self,age):
#         self.age = age

#     def __repr__(self):
#         return f"Dog(name={self.name}, age={self.age})"

# array of objects
# dogs = [Dog("Fido", 3), Dog("Rex", 5)]
# print(dogs[0].get_age())
# q2
# class students:
#     def __init__(self,name,age,grade):
#         self.name = name
#         self.age = age
#         self.grade = grade

#     def get_grade(self):
#         return self.grade
#     def __repr__(self):
#         return f"students(name={self.name}, age={self.age}, grade={self.grade})"

# class course:
#     def __init__(self,name,max_students):
#         self.name = name
#         self.max_students = max_students
#         self.students = []
#     def add_student(self,student):
#         if len(self.students) < self.max_students:
#             self.students.append(student)
#             print(f"✅ Added {student.name} to {self.name}")
#         else:
#             print(f"❌ Cannot add {student.name} to {self.name}: course is full")
#     def get_average_grade(self):
#         val = 0
#         for student in self.students:
#             val += student.get_grade()
#         return val / len(self.students) if self.students else 0

# s1 = students("Alice", 20, 85)
# s2 = students("Bob", 22, 90)
# s3 = students("Charlie", 21, 95)
# course1 = course("Math", 2)
# course1.add_student(s1)
# course1.add_student(s2)
# course1.add_student(s3)  # should fail — course is full
# print(course1.get_average_grade())


# inheritance

# class pet:
#     def __init__(self,name,age):
#         self.name = name
#         self.age = age
#     def show(self):
#         print(f"{self.name} is {self.age} years old.")

# class cat(pet):
#     def __init__(self,name,age,color):
#         super().__init__(name,age)    #need to call the parent class constructor to initialize the inherited attributes
#         self.color = color
#     def speak(self):
#         print(f"{self.name} says Meow!")

# class fish(pet):
#     def __init__(self,name,age,water_type):
#         super().__init__(name,age)
#         self.water_type = water_type
#     def speak(self):
#         print(f"{self.name} says Blub!")

# pet1 = cat("Whiskers", 3, "black")
# pet2 = fish("Nemo", 1, "saltwater")
# pet1.show()
# pet1.speak()
# pet2.show()
# pet2.speak()
# class person:
#     number_of_people = 0

#     def __init__(self, name):
#         self.name = name


# p1 = person("Alice")
# p2 = person("Bob")
# person.number_of_people += 2
# p1.number_of_people += 1
# print(p1.number_of_people)
# print(person.number_of_people)
#Output: 2 why??
# because number_of_people is a class variable,
# it is shared among all instances of the class.
# When you increment person.number_of_people by 2, it updates the class variable for all instances.
# However, when you increment p1.number_of_people by 1, it creates an instance variable for p1 that shadows the class variable.
# Therefore, the output of person.number_of_people remains 2, while p1.number_of_people becomes 3.
#but if you print p2.number_of_people, it will still be 2, because p2 does not have its own instance variable for number_of_people.

# Whereas , in C++, a static member is truly one single memory location — there's no way for p1.number_of_people to "shadow" it.
# p1.number_of_people += 1 modifies the same static variable, so both prints show 3.

class math:
    @staticmethod
    def add(a, b):
        return a + b

    @staticmethod
    def multiply(a, b):
        return a * b
# print(math.add(3, 5))       # Output: 8
# print(math.multiply(3, 5))  # Output: 15
#explanation: The add and multiply methods are defined as static methods using the @staticmethod decorator.
# This means that they can be called directly on the class without needing to create an instance of the class.
# In this example, we call math.add(3, 5) and math.multiply(3, 5) to perform addition and multiplication, respectively.
# but without static method its giving same result because we are calling the method directly on the class,
# which is allowed in Python even without the @staticmethod decorator.
# but if used like m = math() and then m.add(3, 5) it will work only if add is a static method, otherwise it will give an error.
# m = math()
# print(m.add(3, 5))
# print(m.multiply(3, 5))

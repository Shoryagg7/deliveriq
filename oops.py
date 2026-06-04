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

#q2
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

class pet:
    def __init__(self,name,age):
        self.name = name
        self.age = age
    def show(self):
        print(f"{self.name} is {self.age} years old.")

class cat(pet):
    def __init__(self,name,age,color):
        super().__init__(name,age)
        self.color = color
    def speak(self):
        print(f"{self.name} says Meow!")



c1 = cat("Whiskers", 3, "black")
c1.show()   # inherited method
c1.speak()  # cat's own method

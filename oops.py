class Dog:
    def __init__(self, name, breed):
        self.name = name
        self.breed = breed

    def bark(self):
        return f"{self.name} says woof!"

    def __repr__(self):
        return f"Dog(name={self.name}, breed={self.breed})"

buddy = Dog("Buddy", "Golden Retriever")
print(buddy.bark())
print(buddy)


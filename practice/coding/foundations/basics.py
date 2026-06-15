customers = ["John", "Jane", "Bob"]

print(customers[-1])
print(customers[0])

customers.append("Alice")

for customers in customers:
    print(customers)

names = ["john", "jane", "bob"]

uppercase = [name.upper() for name in names]
print(uppercase)
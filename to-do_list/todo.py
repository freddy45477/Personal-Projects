import os


def load_tasks():
    #create an empty list to hold tasks
    tasks = {}
    #check if the tasks.txt exists
    if os.path.exists("tasks.txt"):
        #open the file in read mode
        with open("tasks.txt", "r") as file:
            #for each line in the file
            for line in file:
                #remove the newline character and add task to the list
                tasks.append(line.strip())
    return tasks

#make an empty task list
tasks = load_tasks()

def save_tasks(tasks):
    #open or create a file name tasks.txt in write mode
    with open("tasks.txt", "w") as file:
        #for each task in the task list
        for task in tasks:
            #write each task to the file with a new line
            file.write(task + "\n")

def task_option():
    while True:
        print("1. Add Task\n2. View Tasks\n3. Delete Task\n4. Quit")
        choice = input("What would you like to do?: ")

        if choice == "1":
            task_to_add = input("What task do you want to add?: ")
            tasks.append(f"task: {task_to_add}", "done: {False}")
            save_tasks(tasks) #saves task list after adding
            print("Task added and saved")
        elif choice == "2":
            if tasks == {}:
                print("No tasks available")
            else:
                for i, task in enumerate(tasks, start=1):
                    print (f"{i}. {task}")
                print("\n")
        elif choice == "3":
            task_to_remove = int(input("What do you want to delete?(Number): "))
            found = False
            for i, task in enumerate(tasks, start=1):
                if task_to_remove == i:
                    tasks.remove(task)
                    save_tasks(tasks) #deletes task and save the new task list
                    print ("Task deleted and save")
                    found = True
                    break
                if not found:
                    print ("No task number detected")
            else:
                print("task not found")
        elif choice == "4":
            break
        else:
            print("Invalid Choice")

    
task_option()
    
        
            
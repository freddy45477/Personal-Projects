import os


def load_tasks():
    #create an empty list to hold tasks
    tasks = []
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
        print("(Add/View/Delete/Quit)")
        choice = input("What would you like to do?: ").lower()

        if choice == "add":
            task_to_add = input("What task do you want to add?: ")
            tasks.append(task_to_add)
            save_tasks(tasks) #saves task list after adding
            print("Task added and saved")
        elif choice == "view":
            if tasks == []:
                print("No tasks available")
            else:
                for i, task in enumerate(tasks, start=1):
                    print (f"{i}. {task}")
        elif choice == "delete":
            task_to_remove = input("What do you want to delete?: ")
            if task_to_remove in tasks:
                tasks.remove(task_to_remove)
                save_tasks(tasks) #deletes task and save the new task list
                print ("Task deleted and save")
            else:
                print("task not found")
        elif choice == "quit":
            break
        else:
            print("Invalid Choice")

    
task_option()
    
        
            
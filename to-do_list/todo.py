import os
import json
import datetime


def load_tasks():
    #create an empty list to hold tasks
    tasks = []
    #check if the tasks.txt exists
    if os.path.exists("tasks.txt"):
        #check if file is greater than 0 bytes
        if os.path.getsize("tasks.txt") > 0:

            #open the file in read mode
            with open("tasks.txt", "r") as file:
                #returns a python list or dict
                #file is the object being read
                return json.load(file)
        else:
            #else the file is there, but it is empty
            return tasks
    else:
        #file doesn't exist at all, just return an empty list
        return tasks
        

#make an empty task list
tasks = load_tasks()

def save_tasks(tasks):
    #open or create a file name tasks.txt in write mode
    with open("tasks.txt", "w") as file:
        #json dump converts the python object and turn it into json text and writes it directly to the file
        #task is the data you want to save
        #file is the object where it will be written
        #indent format the json for 4 spcaes
        json.dump(tasks, file, indent=4)

def task_option():
    while True:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("1. Add Task\n2. View Tasks\n3. Delete Task\n4. Mark task as done/undone\n5. Quit")
        choice = input("What would you like to do?: ")

        if choice == "1":
            task_to_add = input("What task do you want to add?: ")
            tasks.append({'task': task_to_add, 'done': False, 'created_at': current_time, 'updated_at': '0000-00-00 00:00:00'})
            save_tasks(tasks) #saves task list after adding
            print("Task added and saved")
        elif choice == "2":
            print("=================")
            print("1. All\n2. Not Done Only\n3. Done Only\n4. Search")
            view_choice = int(input("How do you want to view tasks?: "))

            


            
            filtered_tasks = []

            if tasks == {}:
                print("No tasks available")
            else:
                for i, task in enumerate(tasks, start=1):
                    if view_choice == 1:
                        filtered_tasks = tasks
                    elif view_choice == 2:
                        if task['done'] ==False:
                            filtered_tasks.append(task)
                    elif view_choice == 3:
                        if task['done'] == True:
                            filtered_tasks.append(task)
                    elif view_choice == 4:
                        print("=================")
                        search_input = input("Search Keyword/Letter(Press Enter to skip): ")
                        if search_input == "":
                            pass
                        else:
                            if search_input.lower() in task['task'].lower():
                                filtered_tasks.append(task)
                    else:
                        print("print invalid choice")
                    
                
                
                print("=================")
                print("1. Alphabetically\n2. Creation Date\n3, Update Date\n4. None")
                sort_choice = int(input("How do you want to sort the tasks: "))
                    
                if sort_choice == 1:
                    #sort the tasks alphabetically, lambda is there as an anonymous function (it is just there and needed for sort ot work)
                    #t is the placeholder for each item in your list, t['task'] is  returning the the items with task name 
                    filtered_tasks.sort(key = lambda t:t['task'].lower())
                elif sort_choice == 2:
                    filtered_tasks.sort(key = lambda t:t['created_at'])
                elif sort_choice == 3: 
                    filtered_tasks.sort(key = lambda t:t['updated_at'])
                
                
                print("=================")
                for i, task in enumerate(filtered_tasks, start=1):
                    if task['done'] == True:
                        mark = "✓"
                    else:
                        mark = "✗"
                    print(f"[{mark}] {i}. {task['task']}")
                    print (f"Creation Date: {task['created_at']}")
                    print (f"Updated Date: {task['updated_at']}")
                print("=================")


            
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
                if found == False:
                    print ("No task number detected")
        elif choice == "4":
               print("Your Tasks:")
               print("=================")
               for i, task in enumerate(tasks, start=1):
                    if task['done'] == False:
                        print (f'[✗]{i}.{task['task']}')
                    else:
                        print (f'[✓]{i}.{task['task']}')
               print("=================")
               task_choice = int(input("Press 0 for no changes.\nWhich task number do you want to mark as done or undone?: "))

               if task_choice == 0:
                   continue
               
               index = task_choice - 1
               selected_task = tasks[index]
               if selected_task['done'] == False:
                   selected_task['done'] = True
                   selected_task['updated_at'] = current_time
                   save_tasks(tasks)
               else: 
                   selected_task['done'] = False
                   selected_task['updated_at'] = current_time
                   save_tasks(tasks)
                 
        elif choice == "5":
            break
        
        else:
            print("Invalid Choice")



    
task_option()
    
        
            

# printer spooler problem

## About
This project is about the **printer spooler** problem and its solution  
### what is a printer spooler problem?
Printer spooler problem is a classic synchronization issue, where multiple processes attempt to access a shared resource, \
in this case, a printer.\
<img width="451" height="374" alt="image describing an printer spooler problem" src="https://github.com/user-attachments/assets/e54fad39-48a0-4d9d-8799-bda634ff428f" />

## Solution
My solution is using a doubly LinkedList wtih priority queue. The LinkedList(TaskList) is secured by threading.Lock to have it thread secure. The priority queue is used because some documents needed to be printed sooner than other.

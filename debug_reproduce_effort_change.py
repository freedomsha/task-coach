import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'taskcoach'))
from taskcoachlib.persistence.taskfile import TaskFile
from taskcoachlib.domain import task, effort

# Create a TaskFile and minimal objects
print('Création TaskFile')
tf = TaskFile()
print('Création task1 et task2')
t1 = task.Task()
t2 = task.Task()
print('Ajout task2')
tf.tasks().append(t1)
tf.tasks().append(t2)
print('Création effort lié à t1')
e = effort.Effort(task=t1)
# Ensure effort is in task efforts
print('Efforts de t1 avant:', t1.efforts())
t1.addEffort(e)
print('Efforts de t1 après addEffort:', t1.efforts())
print('Set filename and save')
tf.setFilename('test.tsk')
tf.save()
print('needSave après save:', tf.needSave())
print('Change effort task -> t2')
e.setTask(t2)
print('needSave après setTask:', tf.needSave())
print('done')


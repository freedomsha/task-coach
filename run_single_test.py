import os
import traceback

os.environ['TASKCOACH_TRACE_PUBSUB'] = os.environ.get('TASKCOACH_TRACE_PUBSUB', '1')

from tests.unittests.persistenceTests.TaskFileTest import DirtyTaskFileTest

if __name__ == '__main__':
    test = DirtyTaskFileTest('testNeedSave_AfterEditEffortTask')
    try:
        test.setUp()
        print('\n--- Running testNeedSave_AfterEditEffortTask ---')
        test.testNeedSave_AfterEditEffortTask()
        print('\n--- TEST PASSED ---')
    except Exception as e:
        print('\n--- TEST RAISED EXCEPTION ---')
        traceback.print_exc()
    finally:
        try:
            test.tearDown()
        except Exception:
            pass


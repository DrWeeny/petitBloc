import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(__file__, "../../python")))
from petitBloc import port
from petitBloc import chain
from petitBloc import block
from petitBloc import core
from petitBloc import parameter
from petitBloc import box
from petitBloc import workerManager
import multiprocessing


class DmpStr(block.Block):
    def __init__(self, name=""):
        super(DmpStr, self).__init__(name=name)
        self.dmp = multiprocessing.Queue()

    def initialize(self):
        self.addInput(str)
        self.addParam(str, "testStr")

    def process(self):
        self.dmp.put(self.param("testStr").get())

        return False


class DmpInt(block.Block):
    def __init__(self, name=""):
        super(DmpInt, self).__init__(name=name)
        self.dmp = multiprocessing.Queue()

    def initialize(self):
        self.addInput(int)
        self.addParam(int, "testInt")

    def process(self):
        self.dmp.put(self.param("testInt").get())

        return False


class TestParameter(unittest.TestCase):
    def test_init(self):
        p1 = parameter.Parameter("testStr", value="test")
        self.assertIsNotNone(p1)
        self.assertEqual(p1.typeClass(), str)
        self.assertEqual(str(p1), "Parameter<'testStr'>")
        p2 = parameter.Parameter("testInt", value=1)
        self.assertIsNotNone(p2)
        self.assertEqual(p2.typeClass(), int)
        p3 = parameter.Parameter("testInt", value=1.0)
        self.assertIsNotNone(p3)
        self.assertEqual(p3.typeClass(), float)
        p4 = parameter.Parameter("testBool", value=True)
        self.assertIsNotNone(p4)
        self.assertEqual(p4.typeClass(), bool)

        p5 = parameter.Parameter("castFloat", typeClass=float, value=False)
        self.assertIsNotNone(p5)
        self.assertEqual(p5.typeClass(), float)
        self.assertEqual(p5.get(), 0.0)

        p6 = parameter.Parameter("castBool", typeClass=bool, value=0)
        self.assertIsNotNone(p6)
        self.assertEqual(p6.typeClass(), bool)
        self.assertEqual(p6.get(), False)

        p7 = parameter.Parameter("castStr", typeClass=str, value=0)
        self.assertIsNone(p7)

        p8 = parameter.Parameter("castInt", typeClass=int, value="Asd")
        self.assertIsNone(p8)

        p9 = parameter.Parameter("typeInt", typeClass=int)
        self.assertIsNotNone(p9)

    def test_get_set(self):
        p1 = parameter.Parameter("testStr", str)
        self.assertEqual(p1.get(), "")
        self.assertTrue(p1.set(u"a"))
        self.assertEqual(p1.get(), "a")
        self.assertFalse(p1.set(1))
        p2 = parameter.Parameter("testInt", 0, int)


class TestBlock(unittest.TestCase):
    def test_init(self):
        b = block.Block()
        self.assertIsNotNone(b)

        p = b.addParam()
        self.assertIsNone(p)

        p = b.addParam(str)
        self.assertIsNotNone(p)
        self.assertEqual(p.name(), "param")
        self.assertEqual(p.get(), "")

        p = b.addParam(int)
        self.assertIsNotNone(p)
        self.assertEqual(p.name(), "param1")
        self.assertEqual(p.get(), 0)

        p = b.addParam(float)
        self.assertIsNotNone(p)
        self.assertEqual(p.name(), "param2")
        self.assertEqual(p.get(), 0.0)

        p = b.addParam(bool)
        self.assertIsNotNone(p)
        self.assertEqual(p.name(), "param3")
        self.assertEqual(p.get(), False)

        p = b.addParam(list)
        self.assertIsNone(p)

        p = b.addParam(name="intNumber", value=1)
        self.assertIsNotNone(p)
        self.assertEqual(p.name(), "intNumber")
        self.assertEqual(p.typeClass(), int)
        self.assertEqual(p.get(), 1)

    def test_run(self):
        dmp_str = DmpStr()
        dmp_int = DmpInt()

        self.assertTrue(dmp_str.param("testStr").set("HELLO"))
        self.assertTrue(dmp_int.param("testInt").set(23))
        dmp_str.activate()
        dmp_str.run()

        dmp_int.activate()
        dmp_int.run()

        dmp_str.terminate()
        dmp_int.terminate()

        str_val = []
        while (not dmp_str.dmp.empty()):
            str_val.append(dmp_str.dmp.get())

        self.assertEqual(str_val, ["HELLO"])

        int_val = []
        while (not dmp_int.dmp.empty()):
            int_val.append(dmp_int.dmp.get())

        self.assertEqual(int_val, [23])

    def test_run(self):
        box1 = box.Box()
        dmp_str = DmpStr()
        dmp_int = DmpInt()
        self.assertTrue(box1.addBlock(dmp_str))
        self.assertTrue(box1.addBlock(dmp_int))

        dmp_str.param("testStr").set("HELLO")
        dmp_int.param("testInt").set(23)

        schedule = box1.getSchedule()
        workerManager.WorkerManager.RunSchedule(schedule)

        str_val = []
        while (not dmp_str.dmp.empty()):
            str_val.append(dmp_str.dmp.get())

        self.assertEqual(str_val, ["HELLO"])

        int_val = []
        while (not dmp_int.dmp.empty()):
            int_val.append(dmp_int.dmp.get())

        self.assertEqual(int_val, [23])


if __name__ == "__main__":
    unittest.main()

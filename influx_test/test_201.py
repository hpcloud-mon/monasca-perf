from testbase import TestBase

#Note: there is a definite timing issue on node 1 getting up to date
class test_201(TestBase):
    def run(self):
        self.env.sendSingleMetric(1,self.name,1)
        self.env.sendSingleMetric(2,self.name,2)
        self.env.sendSingleMetric(3,self.name,3)
        if self.env.countMetrics(1,self.name) != 3:
            return ["FAIL","node 1 wrong count"]
        if self.env.countMetrics(2,self.name) != 3:
            return ["FAIL","node 2 wrong count"]
        if self.env.countMetrics(3,self.name) != 3:
            return ["FAIL","node 3 wrong count"]
        self.env.partitionStart(1)
        self.env.fullyPartitionNode(1)
        self.env.sendSingleMetric(2,self.name,4)
        self.env.sendSingleMetric(3,self.name,5)
        if self.env.countMetrics(2,self.name) != 5:
            return ["FAIL","node 1 wrong count 2"]
        if self.env.countMetrics(3,self.name) != 5:
            return ["FAIL","node 2 wrong count 2"]
        self.env.partitionStop(1)
        self.env.sendSingleMetric(1,self.name,6)
        if self.env.countMetrics(2,self.name) != 6:
            return ["FAIL","node 2 wrong count 3"]
        if self.env.countMetrics(3,self.name) != 6:
            return ["FAIL","node 3 wrong count 3"]        
        if self.env.countMetrics(1,self.name) != 6:
            return ["FAIL","node 1 wrong count 3"]
        return ["PASS",""]
    def desc(self):
        return 'Fully partitions away node 1'

# Project Estimation part 2



Goal of this document is to compare actual effort, size and productivity of the project, vs the estimates made in task1.

## Computation of size
Executing `cloc <directory containing py files> --include-lang=Python` we obtained these results:

* 2485 text files.
* 2127 unique files.                                     
* 2753 files ignored.
                                   
| Language | files    | blank    | commment | code     |
| -------- | -------- | -------- | -------- | -------  |
| Python   | 1896     | 121997     |   152844       | 502501 |
| SUM   | 1896     | 121997     |   152844       | 502501 |

        

Compute two separate values of size  
-LOC of production code     `cloc <EzShop\app> --include-lang=Python`: 
* 69 text files.
* 69 unique files.                              
* 115 files ignored.

| Language | files    | blank    | commment | code     |
| -------- | -------- | -------- | -------- | -------  |
| Python   | 69     | 612     |   392       | 2310 |
| SUM   | 69     | 612     |   392       | 2310 |

-LOC of test code      `cloc <EzShop\tests> --include-lang=Python`: 
* 8 text files.
* 8 unique files.                              
* 5 files ignored.

| Language | files    | blank    | commment | code     |
| -------- | -------- | -------- | -------- | -------  |
| Python   | 8     | 706     |   280       | 2552 |
| SUM   | 8     | 706     |   280       | 2552 |

So, the total size of the project is:
```
Total LOC = LOC production + LOC test
Total LOC = 2310 + 2552 = 4862
```


## Computation of effort 
The actual effort was computed by summing all the hours reported in timesheet.md, including all activities carried out during Task 1, Task 2 and Task 3, up to the end of the project on January 18.

The project was developed by 6 team members, and the workload was evenly distributed among them.
Based on the timesheet, each member contributed approximately 50 hours both for projectation and the development, resulting in:
```
Actual effort = 6 × 50 = 300 person-hours
```

## Computation of productivity
Productivity was computed using the following formula:
`productivity = ((LOC of production code)+ (LOC of test code)) / effort`

So, the results are:
```
Productivity = 4862 / 300 ≈ 16.02 LOC/hour
```

## Comparison
|                      | Estimated (end of Task 1) | Actual (Jan 18, end of Task 3) |
| -------------------- | ------------------------- |--------------------------------|
| Production code size | -                   | 2310 LOC                       |
| Test code size       | -                   | 2552 LOC                       |
| Total size           | 18000 LOC                   | 4862 LOC                       |
| Effort               | 2000 hours            | 300 hours                      |
| Productivity         | 10 LOC/hour               | 16.02 LOC/hour                 |


The comparison is meaningful mainly for productivity, since the estimates of size and effort in Task 1 were not based on the official and complete requirements.

In Task 1, the project was estimated as a full-scale EZShop system developed from scratch, assuming a structured development process including documentation, testing, deployment and project management activities. The effort estimated through activity decomposition was 2000 person-hours, with an assumed productivity of 10 LOC/hour.

In the actual project, development started on December 7 and ended on January 18, with a reduced scope and a significantly lower effort. Several activities assumed in Task 1 (such as extensive documentation, deployment and formal project management) were either reduced or not fully performed. Moreover, the project benefited from the use of existing libraries and frameworks and from an evenly distributed workload among 6 team members.

As a consequence, the actual productivity (16.02 LOC/hour) is significantly higher than the initial estimate. This difference does not indicate an error in the original estimation, but rather reflects the different assumptions and scope between the estimated project and the one actually developed during the course.






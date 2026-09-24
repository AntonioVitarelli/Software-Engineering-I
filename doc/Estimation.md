# Project Estimation

Date: 20/11/2025

Version: 2.0.0

# Contents

[Project Estimation](#project-estimation)

- [Estimation approach](#estimation-approach)
- [Estimate by size](#estimate-by-size)
- [Estimate by product decomposition](#estimate-by-product-decomposition)
- [Estimate by activity decomposition + Gantt chart](#estimate-by-activity-decomposition--gantt-chart)
- [Gantt chart](#gantt-chart)
- [Summary](#summary)

# Estimation approach

Consider the EZShop project as described in your requirements document, assume that you are going to develop the project INDEPENDENT of the deadlines of the course, and from scratch.
We are assuming to work in a team of 5 people, 40 working hours/week each

# Estimate by size

|                                                                                                         | Estimate |
| ------------------------------------------------------------------------------------------------------- | -------- |
| NC = Estimated number of classes to be developed                                                        | 150      |
| A = Estimated average size per class, in LOC                                                            | 120      |
| S = Estimated size of project, in LOC (= NC \* A)                                                       | 18000    |
| E = Estimated effort, in person hours (here use productivity 10 LOC per person hour)                    | 1800     |
| C = Estimated cost, in euro (here use 1 person hour cost = 30 euro)                                     | 54000    |
| Estimated calendar time, in calendar weeks (Assume team of 5 people, 8 hours per day, 5 days per week ) | 9        |

# **Estimate by product decomposition**

| component name                                              | Estimated effort (person hours) |
| ----------------------------------------------------------- | ------------------------------- |
| Authentication, authorization and manage accounts(FR1, FR2) | 220                             |
| Manage product and inventory (FR7, FR8)                     | 450                             |
| Manage suppliers and orders (FR4, FR5)                      | 350                             |
| Handle sales and manage refunds (FR6, FR9)                  | 500                             |
| Manage accounting and reporting (FR3)                       | 200                             |
| Logging (FR10)                                              | 80                              |
| **Totale**                                                  | **1.800**                       |

Estimated duration: 9 weeks

# Estimate by activity decomposition + Gantt chart

step 1: activities (WBS), step 2 Gantt chart

| ID        | Activity name                                   | Estimated effort (p/h) |
| --------- | ----------------------------------------------- | ---------------------- |
| A1        | Detailed requirements and documentation updates | 180                    |
| A2        | Architectural design and DB initialization      | 250                    |
| A3        | UI/UX design                                    | 150                    |
| A4        | Backend implementation                          | 650                    |
| A5        | Frontend implementation                         | 350                    |
| A6        | Testing (unit, integration, system)             | 180                    |
| A7        | Deployment and user manuals                     | 80                     |
| A8        | Project management / coordination               | 160                    |
| **Total** |                                                 | **2,000**              |

## Gantt chart

Work breakdown:

- **Week 1**
  - A1 – Detailed requirements specification and documentation update
  - A8 – Project management / coordination
- **Weeks 2–3**
  - A2 – Architectural design and DB initialization
  - A3 – UI/UX design (only W2, may finish within W2)
  - A8 – Project management / coordination
- **Weeks 4–6**
  - A4 – Backend implementation
  - A5 – Frontend implementation (W4–W5)
  - A8 – Project management / coordination
- **Weeks 7–8**
  - A6 – Testing (unit, integration, system)
  - A8 – Project management / coordination
- **Week 9**
  - A7 – Deployment and user manuals
  - A8 – Project management / coordination
- **Week 10**
  - A8 – Project management / coordination + buffer (final bug fixes, refinements)

| ID  | Activity                                                     | 1   | 2   | 3   | 4   | 5   | 6   | 7   | 8   | 9   | 10  |
| --- | ------------------------------------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1  | Detailed requirements specification and documentation update | █   |     |     |     |     |     |     |     |     |     |
| A2  | Architectural design and DB initialization                   |     | █   | █   |     |     |     |     |     |     |     |
| A3  | UI/UX design                                                 |     | █   |     |     |     |     |     |     |     |     |
| A4  | Backend implementation                                       |     |     |     | █   | █   | █   |     |     |     |     |
| A5  | Frontend implementation                                      |     |     |     | █   | █   |     |     |     |     |     |
| A6  | Testing (unit, integration, system)                          |     |     |     |     |     |     | █   | █   |     |     |
| A7  | Deployment and user manuals                                  |     |     |     |     |     |     |     |     | █   |     |
| A8  | Project management / coordination                            | █   | █   | █   | █   | █   | █   | █   | █   | █   | █   |

Estimated duration: 10 weeks

# Summary

Report here the results of the three estimation approaches. The estimates may differ. Discuss here the possible reasons for the difference

|                                    | Estimated effort (ph) | Estimated duration (calendar time) |
| ---------------------------------- | --------------------- | ---------------------------------- |
| estimate by size                   | 1.800                 | 9 weeks                            |
| estimate by product decomposition  | 1.800                 | 9 weeks                            |
| estimate by activity decomposition | 2.000                 | 10 weeks                           |

The **estimate by size** is based only on an overall LOC (Lines Of Code) assumption (18,000 LOC, 10 LOC/hour). It uses a uniform productivity value and does not explicitly account for activities such as meetings, rework, testing overhead or documentation. For this reason it tends to be relatively optimistic.

The **estimate by product decomposition** uses the same total effort (1,800 ph), but distributes it across the main functional components of EZShop (authentication, products/inventory, suppliers/orders, sales/POS, reporting, logging). This approach helps to identify which subsystems are more expensive or risky, but it still focuses mainly on the product and not on the full project lifecycle. Since we calibrated it on the size estimate, the total effort is very similar.

The **estimate by activity decomposition (Gantt)** starts from the project workflow (requirements, design, implementation, testing, deployment, project management). Here we explicitly include testing, deployment, documentation and project management/buffer. As a consequence, the total effort is higher (2,000 ph) and the duration increases to about 10 weeks. This approach is usually more realistic for scheduling, because it models how the team actually spends time, including coordination and non-coding work.

The differences among the three estimates are therefore expected: size-based and product-based estimates are useful for a quick, high-level effort indication, while the activity-based estimate is more detailed and suitable for planning and managing the project timeline.

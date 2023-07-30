# Web Performance Reporter
![main page](https://github.com/sh-alireza/web-performance-reporter/assets/75808544/b7a33d96-6d2c-4fd2-a66e-de7b6eb838d4)

## Description

The Web Performance Reporter is a simple yet powerful tool for website developers seeking to improve website performance. Leveraging the power of Lighthouse through the use of the [lighthouse-python-plus](https://github.com/sh-alireza/lighthouse-python-plus) package. The tool is designed to handle multiple requests to the API with ease, thanks to the use of Celery and RabbitMQ. 
Also this tool can compare the performance of old and new hosts in a single CSV file. This feature makes it easy for developers to see the impact of any changes made to a website and identify areas that require further optimization.

## Usage

```bash
- git clone https://github.com/sh-alireza/web-performance-reporter.git
- cd web-performance-reporter
- docker-compose up --build
```

### lighthouse app:
![lighthouse](https://github.com/sh-alireza/web-performance-reporter/assets/75808544/ff9259de-2378-448d-998f-1ccfe72c61c9)

- host_1 (required): The primary host for performance testing.

- host_2 (optional): Secondary host for comparison with the primary host. Use a new host to compare with the old one.

- priority (optional): Priority check for URLs in the CSV input. If left empty, all URLs will be checked. To check only specific URLs based on their priority value, add the priority value to this parameter.

- form_factor (optional): Choose either "mobile" or "desktop" as the form factor for Lighthouse. The default value is "mobile".

- speed (optional): This parameter sets the Lighthouse environment, including throttling and internet speed. The default settings are based on those found on [pagespeed](https://pagespeed.web.dev/), but you can change them by modifying the MORE_SETTINGS variable in main.py. The available options for speed are "normal", "slow-4g", and leaving it blank for using only Lighthouse's default settings. "Normal" applies all settings with throttling method set to "provided", and "slow-4g" applies all settings with throttling method set to "simulate".

- quiet (optional): Set this parameter to True for debugging purposes when you want to see the logs written by Lighthouse. The default value is False.

- loop (optional): Set this parameter to the number of times you want to run Lighthouse for each URL. For example, if you set it to 3, Lighthouse will run 3 times and return the mean of the results.

- input_urls (required): This parameter requires a CSV file in the format shown in the [sample_inputs](sample_inputs.csv) file in this repository.

### output:
![output](https://github.com/sh-alireza/web-performance-reporter/assets/75808544/0537a64a-0f62-4f47-b44b-de0b10d790aa)

The output will consist of a task ID and a static output file link.

### status:
![status](https://github.com/sh-alireza/web-performance-reporter/assets/75808544/8c86c4e5-e3f6-4b33-85f5-3a027d47a383)

You can use the provided task ID to check its status, which can be pending, failed, or successful.

### pending tasks:
![pending tasks](https://github.com/sh-alireza/web-performance-reporter/assets/75808544/2a2d4747-4c73-4cee-889a-96d2d7bfa3d0)


You can view all pending tasks and their corresponding task IDs.

### delete task:
![delete task](https://github.com/sh-alireza/web-performance-reporter/assets/75808544/e1fbbcff-e0fa-423d-aa1e-cb4d382fc2d4)


You can delete a task using its corresponding task ID.

## Changes
[You can find all changes in CHANGELOG!](CHANGELOG.md)

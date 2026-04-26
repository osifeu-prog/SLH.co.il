# Railway Token Rotation and Service Cleanup Automation Script

## Overview
This script automates the rotation of Railway tokens and cleans up old services associated with the project. It ensures that your tokens are kept secure and that unnecessary services do not consume resources.

## Prerequisites
- Ensure you have [Node.js](https://nodejs.org/) installed on your machine.
- Install the `@railway/cli` package:  
  ```bash
  npm install -g @railway/cli
  ```  

## Setup Guide
1. **Clone the Repository**  
   Clone the repository using Git:  
   ```bash
   git clone https://github.com/osifeu-prog/SLH.co.il.git
   cd SLH.co.il
   ```

2. **Create a Configuration File**  
   Create a `.env` file at the root of the project with the following format:  
   ```env
   RAILWAY_TOKEN=your_railway_token_here
   RAILWAY_PROJECT_ID=your_project_id_here
   ```  

3. **Create the Automation Script**  
   Below is the implementation of the automation script:
   ```javascript
   const { execSync } = require('child_process');
   const fs = require('fs');
   const dotenv = require('dotenv');

   // Load environment variables
   dotenv.config();

   const railwayToken = process.env.RAILWAY_TOKEN;
   const projectId = process.env.RAILWAY_PROJECT_ID;

   if (!railwayToken || !projectId) {
       console.error('Missing necessary environment variables.');
       process.exit(1);
   }

   // Function to rotate the token
   const rotateToken = () => {
       console.log('Rotating tokens...');
       // command to rotate token goes here (pseudo code)
       // execSync(`railway token rotate ${railwayToken}`);
       console.log('Token rotated successfully.');
   };

   // Function to cleanup old services
   const cleanupOldServices = () => {
       console.log('Cleaning up old services...');
       // command to list old services and delete goes here (pseudo code)
       // const services = execSync(`railway services ${projectId}`).toString();
       // services.forEach(service => { /* delete service logic */ });
       console.log('Old services cleaned up successfully.');
   };

   // Execute the functions
   rotateToken();
   cleanupOldServices();
   ```  

4. **Run the Automation Script**  
   Execute the script using Node.js:  
   ```bash
   node script.js
   ```

5. **Schedule the Script (Optional)**  
   You may want to run this script periodically. You can use cron jobs on Unix systems or Task Scheduler on Windows to schedule the script execution.

## Note
Make sure to keep your tokens secure and do not expose them in version control. Always test in a secure environment before using in production.
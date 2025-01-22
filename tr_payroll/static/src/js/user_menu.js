// /** @odoo-module **/
// import { registry } from "@web/core/registry";
// import { browser } from "@web/core/browser/browser";
// import rpc from 'web.rpc';

// const userMenuRegistry = registry.category("user_menuitems");

// let profileItem = {
//     type: "item",
//     id: "my_profile",
//     description: "Loading My Profile...",
//     sequence: 10,
//     callback: () => {}, // No action initially
// };

// // Add placeholder to the registry
// userMenuRegistry.add("my_profile", () => profileItem);

// async function updateMyProfileItem(env) {
//     console.log('Fetching action ID for "My Profile Wizard"...');

//     const actionId = await rpc.query({
//         model: 'payroll.my.profile.wizard',
//         method: 'search_read',
//         args: [[]],  // Search for all records (if needed, you can add domain filters)
//         kwargs: {
//             context: { sudo: true },
//         },
//     }).then(records => {
//         console.log('Profile wizard records:', records);
//         return records.length ? records[0].value_ir_action_wizard : null;  // Directly use the value_ir_action_wizard field
//     }).catch(error => {
//         console.error('Error fetching action ID:', error);
//         return null;
//     });

//     if (!actionId) {
//         console.error('Action ID not found in payroll.my.profile.wizard.');
//         return;
//     }

//     console.log('Action ID:', actionId);
//     const profileURL = `/web#action=${actionId}&model=payroll.my.profile.wizard&view_type=form`;
//     // const profileURL = `/web#action=275&model=payroll.my.profile.wizard&view_type=form`;

//     profileItem.description = "My Profile";  
//     profileItem.href = profileURL;       
//     profileItem.callback = () => {
//         browser.open(profileURL, "_self");  
//     };

//     console.log("Updated My Profile menu item!");
// }

// updateMyProfileItem();

/** @odoo-module **/
// Harcode id
import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";

const userMenuRegistry = registry.category("user_menuitems");

function myProfileItem(env) {
    const profileURL = "/web#action=274&model=payroll.my.profile.wizard&view_type=form";
    return {
        type: "item",
        id: "user_profile",
        description: env._t("My Profile"),
        href: profileURL,
        callback: () => {
            browser.open(profileURL, "_self");
        },
        sequence: 10,
    };
}

userMenuRegistry.add("user_profile", myProfileItem);

// JavaScript ReDoS (Regular Expression Denial of Service) & Unchecked Object Merge
const EMAIL_REGEX = /^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/;

function validateEmail(email) {
    // VULN: Exponential backtracking on malicious input like: "aaaaaaaaaaaaaaaaaaaaaaaaaaaa!"
    return EMAIL_REGEX.test(email);
}

function mergeUserData(target, source) {
    // VULN: Prototype Pollution risk
    for (let key in source) {
        if (typeof source[key] === 'object' && source[key] !== null) {
            if (!target[key]) target[key] = {};
            mergeUserData(target[key], source[key]);
        } else {
            target[key] = source[key];
        }
    }
    return target;
}

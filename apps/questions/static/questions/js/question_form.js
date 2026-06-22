// Question form - choice management

const formset = document.getElementById('choice-formset');
const addButton = document.getElementById('add-choice');
const totalForms = document.getElementById('id_choices-TOTAL_FORMS');
const template = document.getElementById('choice-template');

let formIndex = parseInt(totalForms.value);

// Renumber form fields to match DOM order
function renumberForms() {
    const choices = formset.querySelectorAll('.choice-form');
    choices.forEach((choice, index) => {
        // Update all input/textarea names and IDs
        const inputs = choice.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            const name = input.getAttribute('name');
            const id = input.getAttribute('id');
            
            if (name) {
                // Replace choices-X- with choices-{index}-
                const newName = name.replace(/choices-\d+-/, `choices-${index}-`);
                input.setAttribute('name', newName);
            }
            
            if (id) {
                const newId = id.replace(/choices-\d+-/, `choices-${index}-`);
                input.setAttribute('id', newId);
            }
        });
        
        // Update label for attributes
        const labels = choice.querySelectorAll('label');
        labels.forEach(label => {
            const forAttr = label.getAttribute('for');
            if (forAttr) {
                const newFor = forAttr.replace(/choices-\d+-/, `choices-${index}-`);
                label.setAttribute('for', newFor);
            }
        });
    });
    
    // Update total forms count
    totalForms.value = choices.length;
}

// Update choice numbering and correct badge
function updateChoiceNumbers() {
    const choices = formset.querySelectorAll('.choice-form');
    choices.forEach((choice, index) => {
        // Update number badge
        const numberBadge = choice.querySelector('.choice-number');
        if (numberBadge) numberBadge.textContent = index + 1;
        
        // Show/hide correct answer badge
        const correctBadge = choice.querySelector('.correct-badge');
        if (correctBadge) {
            correctBadge.style.display = index === 0 ? 'inline-block' : 'none';
        }
        
        // Enable/disable move buttons
        const moveUp = choice.querySelector('.move-up');
        const moveDown = choice.querySelector('.move-down');
        if (moveUp) moveUp.disabled = index === 0;
        if (moveDown) moveDown.disabled = index === choices.length - 1;
    });
    
    // Renumber forms after updating
    renumberForms();
}

// Add new choice
addButton.addEventListener('click', function() {
    const newForm = template.content.cloneNode(true);
    const formDiv = newForm.querySelector('.choice-form');
    
    // Replace __prefix__ with actual index
    formDiv.innerHTML = formDiv.innerHTML.replace(/__prefix__/g, formIndex);
    formDiv.dataset.choiceIndex = formIndex;
    
    formset.appendChild(formDiv);
    formIndex++;
    
    updateChoiceNumbers();
    attachChoiceEvents(formDiv);
});

// Attach events to a choice form
function attachChoiceEvents(choiceForm) {
    // Move up
    choiceForm.querySelector('.move-up').addEventListener('click', function() {
        const prev = choiceForm.previousElementSibling;
        if (prev) {
            formset.insertBefore(choiceForm, prev);
            updateChoiceNumbers();
        }
    });
    
    // Move down
    choiceForm.querySelector('.move-down').addEventListener('click', function() {
        const next = choiceForm.nextElementSibling;
        if (next) {
            formset.insertBefore(next, choiceForm);
            updateChoiceNumbers();
        }
    });
    
    // Delete
    choiceForm.querySelector('.delete-choice').addEventListener('click', function() {
        if (formset.querySelectorAll('.choice-form').length <= 2) {
            alert('You must have at least 2 choices.');
            return;
        }
        choiceForm.remove();
        updateChoiceNumbers();
    });
}

// Attach events to existing choices
formset.querySelectorAll('.choice-form').forEach(attachChoiceEvents);

// Initial numbering
updateChoiceNumbers();


// ==================== VARIABLE MANAGEMENT ====================

// Cache DOM references
const variableList = document.getElementById('variable-list');
const addVariableBtn = document.getElementById('add-variable-btn');
const variableRowTemplate = document.getElementById('variable-row-template');
const variablesJsonInput = document.getElementById('id_variables_json');
const questionForm = document.querySelector('form');

let variableCounter = 0;

// Add new variable
function addVariable(name = '', type = 'num', config = {}) {
    const newRow = variableRowTemplate.content.cloneNode(true);
    const rowDiv = newRow.querySelector('.variable-row');
    
    // Set unique ID
    const varId = `var-${variableCounter++}`;
    rowDiv.dataset.varId = varId;
    
    // Set values if provided (before appending to DOM)
    const nameInput = rowDiv.querySelector('.variable-name');
    const typeSelect = rowDiv.querySelector('.variable-type');
    
    if (name) nameInput.value = name;
    typeSelect.value = type;
    
    // Add to DOM
    variableList.appendChild(newRow);
    
    // Now query from the actual rowDiv in the DOM
    const typeSelectInDom = rowDiv.querySelector('.variable-type');
    
    // Update fields for selected type
    updateVariableFields(typeSelectInDom);
    
    // Set config values if provided
    if (Object.keys(config).length > 0) {
        setVariableConfig(rowDiv, type, config);
    }
    
    // Attach event listeners
    attachVariableEvents(rowDiv);
    
    return rowDiv;
}

// Remove variable
function removeVariable(button) {
    const row = button.closest('.variable-row');
    row.remove();
}

// Update fields based on variable type
function updateVariableFields(typeSelect) {
    const row = typeSelect.closest('.variable-row');
    const fieldsContainer = row.querySelector('.variable-fields');
    const selectedType = typeSelect.value;
    
    // Clear existing fields
    fieldsContainer.innerHTML = '';
    
    // Get appropriate template
    const templateId = `fields-${selectedType}-template`;
    const template = document.getElementById(templateId);
    
    if (template) {
        const fields = template.content.cloneNode(true);
        fieldsContainer.appendChild(fields);
    }
}

// Set config values for a variable
function setVariableConfig(row, type, config) {
    if (type === 'num') {
        const minInput = row.querySelector('.var-min');
        const maxInput = row.querySelector('.var-max');
        const precisionInput = row.querySelector('.var-precision');
        
        if (minInput && config.min !== undefined) minInput.value = config.min;
        if (maxInput && config.max !== undefined) maxInput.value = config.max;
        if (precisionInput && config.precision !== undefined) precisionInput.value = config.precision;
    } else if (type === 'string') {
        const valuesInput = row.querySelector('.var-values');

        if (valuesInput && config.values) valuesInput.value = config.values.join('\n');
    } else if (type === 'set') {
        const itemsInput = row.querySelector('.var-items');
        const sizeInput = row.querySelector('.var-size');
        
        if (itemsInput && config.items) itemsInput.value = config.items.join('\n');
        if (sizeInput && config.size !== undefined) sizeInput.value = config.size;
    } else if (type === 'expression') {
        const formulaInput = row.querySelector('.var-formula');
        
        if (formulaInput && config.formula) formulaInput.value = config.formula;
    }
}

// Serialize all variables to JSON
function serializeVariables() {
    const variables = {};
    const rows = variableList.querySelectorAll('.variable-row');
    
    rows.forEach(row => {
        const nameInput = row.querySelector('.variable-name');
        const typeSelect = row.querySelector('.variable-type');
        
        const name = nameInput.value.trim();
        const type = typeSelect.value;
        
        if (!name) return; // Skip empty names
        
        const config = { type };
        
        // Get type-specific config
        if (type === 'num') {
            const minInput = row.querySelector('.var-min');
            const maxInput = row.querySelector('.var-max');
            const precisionInput = row.querySelector('.var-precision');
            
            config.min = parseFloat(minInput.value) || 0;
            config.max = parseFloat(maxInput.value) || 100;
            config.precision = parseFloat(precisionInput.value) || 1;
        } else if (type === 'string') {
            const valuesInput = row.querySelector('.var-values');

            const valuesText = valuesInput.value.trim();
            config.values = valuesText ? valuesText.split(/\r?\n/).map(s => s.trim()).filter(s => s) : [];
        } else if (type === 'set') {
            const itemsInput = row.querySelector('.var-items');
            const sizeInput = row.querySelector('.var-size');
            
            const itemsText = itemsInput.value.trim();
            config.items = itemsText ? itemsText.split(/\r?\n/).map(s => s.trim()).filter(s => s) : [];
            config.size = parseInt(sizeInput.value) || 1;
        } else if (type === 'expression') {
            const formulaInput = row.querySelector('.var-formula');
            
            config.formula = formulaInput.value.trim();
        }
        
        variables[name] = config;
    });
    
    return variables;
}

// Load existing variables (for edit mode)
function loadVariables(variablesJson) {
    if (!variablesJson || typeof variablesJson !== 'object') return;
    
    // Add each variable
    for (const [name, config] of Object.entries(variablesJson)) {
        const type = config.type || 'num';
        const configCopy = { ...config };
        delete configCopy.type;
        
        addVariable(name, type, configCopy);
    }
}

// Attach event listeners to a variable row
function attachVariableEvents(row) {
    // Type change
    const typeSelect = row.querySelector('.variable-type');
    typeSelect.addEventListener('change', function() {
        updateVariableFields(this);
    });
    
    // Remove button
    const removeBtn = row.querySelector('.remove-variable');
    removeBtn.addEventListener('click', function() {
        removeVariable(this);
    });
}

// Add variable button click
if (addVariableBtn) {
    addVariableBtn.addEventListener('click', function() {
        addVariable();
    });
}

// Form submit - serialize variables to hidden input
if (questionForm && variablesJsonInput) {
    questionForm.addEventListener('submit', function(e) {
        const variables = serializeVariables();
        variablesJsonInput.value = JSON.stringify(variables);
    });
}

// Load existing variables on page load
if (variablesJsonInput && variablesJsonInput.value) {
    try {
        const existing = JSON.parse(variablesJsonInput.value);
        loadVariables(existing);
    } catch (e) {
        console.error('Failed to parse existing variables:', e);
    }
}

// ==================== VALIDATION RULES MANAGEMENT ====================

const rulesList = document.getElementById('validation-rules-list');
const addRuleBtn = document.getElementById('add-rule-btn');
const ruleTemplate = document.getElementById('validation-rule-template');
const validationRulesInput = document.getElementById('id_validation_rules_json');

// Add a new validation rule row
function addValidationRule(expression = '') {
    if (!ruleTemplate || !rulesList) return;
    
    const clone = ruleTemplate.content.cloneNode(true);
    const row = clone.querySelector('.validation-rule-row');
    
    // Set expression if provided
    if (expression) {
        const input = clone.querySelector('.rule-expression');
        input.value = expression;
    }
    
    // Attach events
    const removeBtn = clone.querySelector('.remove-rule');
    removeBtn.addEventListener('click', function() {
        row.remove();
    });
    
    rulesList.appendChild(clone);
}

// Serialize all validation rules to array
function serializeValidationRules() {
    if (!rulesList) return [];
    
    const rules = [];
    const rows = rulesList.querySelectorAll('.validation-rule-row');
    
    rows.forEach(row => {
        const expression = row.querySelector('.rule-expression').value.trim();
        if (expression) {
            rules.push(expression);
        }
    });
    
    return rules;
}

// Load existing validation rules
function loadValidationRules(rulesArray) {
    if (!Array.isArray(rulesArray)) return;
    
    // Clear existing
    if (rulesList) {
        rulesList.innerHTML = '';
    }
    
    // Add each rule
    rulesArray.forEach(expression => {
        addValidationRule(expression);
    });
}

// Add rule button click
if (addRuleBtn) {
    addRuleBtn.addEventListener('click', function() {
        addValidationRule();
    });
}

// Form submit - serialize rules to hidden input
if (questionForm && validationRulesInput) {
    questionForm.addEventListener('submit', function(e) {
        const rules = serializeValidationRules();
        validationRulesInput.value = JSON.stringify(rules);
    });
}

// Load existing rules on page load
if (validationRulesInput && validationRulesInput.value) {
    try {
        const existing = JSON.parse(validationRulesInput.value);
        loadValidationRules(existing);
    } catch (e) {
        console.error('Failed to parse existing validation rules:', e);
    }
}

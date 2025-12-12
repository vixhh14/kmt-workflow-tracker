/**
 * Dropdown Debug Utility
 * Use this to debug dropdown data loading issues
 */

export const debugDropdownData = (componentName, dataName, data) => {
    console.group(`🔍 Dropdown Debug: ${componentName} - ${dataName}`);
    console.log('Data Type:', typeof data);
    console.log('Is Array:', Array.isArray(data));
    console.log('Data Length:', data?.length);
    console.log('Data Sample:', data?.slice(0, 3));
    console.log('Full Data:', data);
    console.groupEnd();
};

export const debugAPIResponse = (apiName, response) => {
    console.group(`📡 API Response: ${apiName}`);
    console.log('Response Type:', typeof response);
    console.log('Response Data:', response?.data);
    console.log('Data Type:', typeof response?.data);
    console.log('Is Array:', Array.isArray(response?.data));
    console.log('Data Length:', response?.data?.length);
    console.groupEnd();
};

export const validateDropdownData = (dataArray, requiredFields = []) => {
    if (!Array.isArray(dataArray)) {
        console.error('❌ Data is not an array:', dataArray);
        return false;
    }

    if (dataArray.length === 0) {
        console.warn('⚠️ Data array is empty');
        return true; // Empty is valid, just no options
    }

    const firstItem = dataArray[0];
    const missingFields = requiredFields.filter(field => !(field in firstItem));

    if (missingFields.length > 0) {
        console.error('❌ Missing required fields:', missingFields);
        console.log('First item:', firstItem);
        return false;
    }

    console.log('✅ Data validation passed');
    return true;
};

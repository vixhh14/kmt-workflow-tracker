/**
 * Normalizes machine name resolution across the application.
 * Follows the priority: name -> machine_name -> display_name -> Unnamed Machine
 */
export const resolveMachineName = (machine) => {
    if (!machine) return "Unnamed Machine";

    const name = machine.name || machine.machine_name || machine.display_name;
    if (name && name !== 'Unknown' && name !== 'Unknown Machine') return name;

    if (machine.id) return `Machine-${machine.id}`;

    return "Unnamed Machine";
};

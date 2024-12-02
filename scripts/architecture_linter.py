import os
import ast
import sys
import re

class ArchitectureLinter:
    """
    Custom linter to enforce architectural constraints:
    1. Features modules cannot import other features modules
    2. Core modules are globally accessible
    """

    def __init__(self, root_path):
        self.root_path = root_path
        self.features_path = os.path.join(root_path, 'features')
        self.core_path = os.path.join(root_path, 'core')

    def is_features_module(self, module_path):
        """Check if a module is within the features directory."""
        return self.features_path in module_path

    def is_core_module(self, module_path):
        """Check if a module is within the core directory."""
        return self.core_path in module_path

    def check_import_constraints(self, file_path):
        """
        Check import constraints for a given file.
        
        Returns:
        - List of violations
        """
        violations = []

        # Try multiple encodings
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    tree = ast.parse(content)
                    break
            except (UnicodeDecodeError, SyntaxError):
                if encoding == encodings_to_try[-1]:
                    # If all encodings fail, skip this file
                    print(f"Warning: Could not parse {file_path} with any encoding")
                    return violations

        # Collect all import statements
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)

        for imp in imports:
            if isinstance(imp, ast.Import):
                for alias in imp.names:
                    module_name = alias.name
                    module_path = self._resolve_module_path(module_name, file_path)
                    
                    # Check features module cross-import
                    if (self.is_features_module(file_path) and 
                        self.is_features_module(module_path) and 
                        os.path.dirname(file_path) != os.path.dirname(module_path)):
                        violations.append(
                            f"Violation: Features module {file_path} imports another features module {module_path}"
                        )

            elif isinstance(imp, ast.ImportFrom):
                module_name = imp.module or ''
                full_module_name = module_name
                
                # Resolve relative imports
                if imp.level > 0:
                    full_module_name = self._resolve_relative_import(file_path, module_name, imp.level)
                
                module_path = self._resolve_module_path(full_module_name, file_path)
                
                # Check features module cross-import
                if (self.is_features_module(file_path) and 
                    self.is_features_module(module_path) and 
                    os.path.dirname(file_path) != os.path.dirname(module_path)):
                    violations.append(
                        f"Violation: Features module {file_path} imports another features module {module_path}"
                    )

        return violations

    def _resolve_relative_import(self, current_file, module_name, level):
        """Resolve relative import to full module path."""
        current_dir = os.path.dirname(current_file)
        for _ in range(level - 1):
            current_dir = os.path.dirname(current_dir)
        
        if module_name:
            return os.path.join(current_dir, module_name).replace('/', '.').replace('\\', '.')
        return current_dir.replace('/', '.').replace('\\', '.')

    def _resolve_module_path(self, module_name, current_file):
        """
        Resolve a module name to its full file path.
        
        This is a simplified version and might need more sophisticated 
        resolution in complex projects.
        """
        try:
            # Try to find the module in the project
            parts = module_name.split('.')
            potential_paths = [
                os.path.join(self.root_path, *parts) + '.py',
                os.path.join(self.root_path, *parts, '__init__.py')
            ]
            
            for path in potential_paths:
                if os.path.exists(path):
                    return path
            
            # Fallback: if not found in project, assume it's a standard library or installed package
            return ''
        except Exception:
            return ''

    def lint_project(self):
        """
        Lint the entire project for architectural constraints.
        
        Returns:
        - List of all violations
        """
        all_violations = []
        
        for root, _, files in os.walk(self.root_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    # Ignore test files and the linter itself
                    if 'tests' in file_path or 'scripts/architecture_linter.py' in file_path:
                        continue
                    violations = self.check_import_constraints(file_path)
                    if violations:
                        all_violations.extend(violations)
        
        return all_violations

def main():
    """Main entry point for the architecture linter."""
    if len(sys.argv) < 2:
        print("Usage: python architecture_linter.py /path/to/project")
        sys.exit(1)
    
    project_root = sys.argv[1]
    linter = ArchitectureLinter(project_root)
    
    violations = linter.lint_project()
    
    if violations:
        print("Architectural Violations Found:")
        for violation in violations:
            print(violation)
        sys.exit(1)
    else:
        print("No architectural violations found.")
        sys.exit(0)

if __name__ == '__main__':
    main()

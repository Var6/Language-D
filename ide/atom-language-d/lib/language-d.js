'use strict';

const { CompositeDisposable } = require('atom');
const { exec } = require('child_process');
const path = require('path');

function activeFile() {
  const editor = atom.workspace.getActiveTextEditor();
  if (!editor) {
    atom.notifications.addError('Language D: no active editor');
    return null;
  }

  const filePath = editor.getPath();
  if (!filePath) {
    atom.notifications.addError('Language D: save the file first');
    return null;
  }

  if (path.extname(filePath) !== '.d') {
    atom.notifications.addError('Language D: only .d files are supported');
    return null;
  }

  editor.save();
  return filePath;
}

function projectRoot(filePath) {
  return path.resolve(path.dirname(filePath), '..');
}

function runCommand(command, cwd, title) {
  exec(command, { cwd }, (error, stdout, stderr) => {
    const output = [stdout, stderr].filter(Boolean).join('\n').trim();
    if (error) {
      atom.notifications.addError(title, {
        detail: output || error.message,
        dismissable: true
      });
      return;
    }

    atom.notifications.addSuccess(title, {
      detail: output || 'Done',
      dismissable: true
    });
  });
}

module.exports = {
  subscriptions: null,

  activate() {
    this.subscriptions = new CompositeDisposable();

    this.subscriptions.add(atom.commands.add('atom-workspace', {
      'language-d:check': () => this.check(),
      'language-d:run': () => this.run(),
      'language-d:compile-cpp': () => this.compileCpp(),
      'language-d:build-native': () => this.buildNative()
    }));
  },

  deactivate() {
    if (this.subscriptions) {
      this.subscriptions.dispose();
      this.subscriptions = null;
    }
  },

  check() {
    const filePath = activeFile();
    if (!filePath) {
      return;
    }
    const root = projectRoot(filePath);
    runCommand(`python langd.py check "${filePath}"`, root, 'Language D check passed');
  },

  run() {
    const filePath = activeFile();
    if (!filePath) {
      return;
    }
    const root = projectRoot(filePath);
    runCommand(`python langd.py run "${filePath}"`, root, 'Language D program finished');
  },

  compileCpp() {
    const filePath = activeFile();
    if (!filePath) {
      return;
    }
    const root = projectRoot(filePath);
    const outputFile = path.join(root, 'build', `${path.basename(filePath, '.d')}.cpp`);
    runCommand(`python langd.py compile-cpp "${filePath}" -o "${outputFile}"`, root, 'Language D C++ generated');
  },

  buildNative() {
    const filePath = activeFile();
    if (!filePath) {
      return;
    }
    const root = projectRoot(filePath);
    const base = path.basename(filePath, '.d');
    const cppFile = path.join(root, 'build', `${base}.cpp`);
    const exeFile = path.join(root, 'build', `${base}.exe`);
    runCommand(
      `python langd.py compile-cpp "${filePath}" -o "${cppFile}" && g++ -std=c++20 "${cppFile}" -o "${exeFile}" && "${exeFile}"`,
      root,
      'Language D native build finished'
    );
  }
};

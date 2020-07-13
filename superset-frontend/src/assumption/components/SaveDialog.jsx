import React, { useState } from 'react';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import PreLoader from '../../components/PreLoader';

function SaveDialog({
  open,
  handleClose,
  columns,
  data,
  saveTableData,
  table,
}) {
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);

  // console.log(data);

  const handleNoteChange = event => {
    setNote(event.target.value);
  };

  const handleSaveTableData = () => {
    setSaving(true);

    saveTableData(
      table,
      {
        data,
        header: columns.map(c => c.title),
      },
      note,
    );
  };

  return (
    <div>
      <Dialog
        fullWidth
        maxWidth="sm"
        open={open}
        onClose={handleClose}
        disableBackdropClick
        disableEscapeKeyDown
        aria-labelledby="form-dialog-title"
      >
        <DialogTitle id="form-dialog-title">Save</DialogTitle>
        <DialogContent>
          <DialogContentText>
            To save the changes, please enter your note about this modify.
          </DialogContentText>
          <TextField
            required
            autoFocus
            margin="dense"
            id="note"
            label="Required"
            value={note}
            placeholder="Write your note about this modify"
            fullWidth
            onChange={handleNoteChange}
          />
        </DialogContent>
        <DialogActions>
          <Button disabled={saving} onClick={handleClose} color="primary">
            Cancel
          </Button>
          <Button
            disabled={note === ''}
            onClick={handleSaveTableData}
            color="primary"
          >
            {saving ? (
              <div style={{ width: 39.68 }}>
                <PreLoader />
              </div>
            ) : (
              'Save'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default SaveDialog;

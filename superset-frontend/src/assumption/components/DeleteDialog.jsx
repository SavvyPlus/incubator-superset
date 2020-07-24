import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

function DeleteDialog({ open, data, handleClose, handleDeleteSelected }) {
  const classes = useStyles();

  const getKeys = d => {
    return Object.keys(d[0]);
  };

  const createTableRows = d => {
    const rows = [];
    const keys = getKeys(d);

    for (let i = 0; i < d.length; i++) {
      const row = [];
      for (let j = 0; j < keys.length; j++) {
        if (keys[j] !== 'tableData') {
          if (d[i][keys[j]] instanceof Date) {
            const dateObj = d[i][keys[j]];
            row.push(
              <TableCell key={keys[j]}>
                {`${`0${dateObj.getDate()}`.slice(-2)}/${`0${`0${
                  dateObj.getMonth() + 1
                }`.slice(-2)}`.slice(-2)}/${dateObj.getFullYear()}`}
              </TableCell>,
            );
          } else {
            row.push(<TableCell key={keys[j]}>{d[i][keys[j]]}</TableCell>);
          }
        }
      }
      rows.push(<TableRow key={i}>{row}</TableRow>);
    }
    return rows;
  };

  return (
    <div>
      <Dialog
        maxWidth="md"
        open={open}
        onClose={handleClose}
        aria-labelledby="form-dialog-title"
      >
        <DialogTitle id="form-dialog-title">Delete Table Rows?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {`The following ${data.length} table rows will be deleted:`}
          </DialogContentText>
          {data.length > 0 && (
            <TableContainer component={Paper}>
              <Table
                className={classes.table}
                size="small"
                aria-label="a dense table"
              >
                <TableHead>
                  <TableRow>
                    {getKeys(data).map(
                      k =>
                        k !== 'tableData' && <TableCell key={k}>{k}</TableCell>,
                    )}
                  </TableRow>
                </TableHead>
                <TableBody>{createTableRows(data)}</TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} color="primary">
            Cancel
          </Button>
          <Button onClick={handleDeleteSelected} color="primary">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default DeleteDialog;
